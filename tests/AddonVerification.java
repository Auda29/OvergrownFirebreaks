package firebreaks.verification;

import com.google.gson.*;
import java.io.*;
import java.lang.reflect.*;
import java.nio.file.*;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.fml.ModList;

@Mod("overgrown_firebreaks_verification")
public final class AddonVerification {
    public AddonVerification() {
        NeoForge.EVENT_BUS.addListener(this::started);
        NeoForge.EVENT_BUS.addListener(this::tick);
    }

    private static Method singleMethod(Class<?> owner, String name, int count) {
        for (Method m : owner.getMethods()) {
            if (m.getName().equals(name) && m.getParameterCount() == count) return m;
        }
        throw new IllegalStateException("Missing method " + owner + "." + name);
    }

    private void started(ServerStartedEvent event) {
        verify(event);
    }

    private void tick(ServerTickEvent.Post event) {
        if (Files.exists(Path.of("verify-again.flag"))) {
            try { Files.delete(Path.of("verify-again.flag")); } catch (IOException e) { throw new RuntimeException(e); }
            verify(event);
        }
        if (Files.exists(Path.of("fire-check.flag"))) {
            try { Files.delete(Path.of("fire-check.flag")); } catch (IOException e) { throw new RuntimeException(e); }
            verifyFire(event);
        }
    }

    private void verifyFire(Object event) {
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(Path.of("fire-results.txt")))) {
            Object server = event.getClass().getMethod("getServer").invoke(event);
            Object level = server.getClass().getMethod("overworld").invoke(server);
            Class<?> pos = Class.forName("net.minecraft.core.BlockPos");
            Method getState = level.getClass().getMethod("getBlockState", pos);
            Method getBlock = Class.forName("net.minecraft.world.level.block.state.BlockState").getMethod("getBlock");
            Object registry = Class.forName("net.minecraft.core.registries.BuiltInRegistries").getField("BLOCK").get(null);
            Method key = singleMethod(Class.forName("net.minecraft.core.Registry"), "getKey", 1);
            boolean pass = true;
            for (int x : new int[]{0, 4, 8, 12}) {
                Object state = getState.invoke(level, pos.getConstructor(int.class, int.class, int.class).newInstance(x, 65, 0));
                String actual = key.invoke(registry, getBlock.invoke(state)).toString();
                boolean valid = x < 8 ? actual.startsWith("burnt:") : actual.equals("minecraft:air");
                pass &= valid;
                out.println((valid ? "PASS" : "WAIT") + " actual fire at x=" + x + ": " + actual);
            }
            out.println(pass ? "RESULT PASS" : "RESULT WAIT");
            if (pass) System.out.println("FIREBREAKS_FIRE PASS");
        } catch (Throwable e) {
            e.printStackTrace();
        }
    }

    private void verify(Object event) {
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(Path.of("verification-results.txt")))) {
            try {
                JsonObject expected = JsonParser.parseReader(Files.newBufferedReader(Path.of(System.getProperty("firebreaks.expectations")))).getAsJsonObject();
                boolean protection = Boolean.getBoolean("firebreaks.protection");
                if (!ModList.get().isLoaded("overgrown_firebreaks")) throw new AssertionError("Core addon not loaded");
                if (ModList.get().isLoaded("overgrown_firebreaks_protection") != protection) throw new AssertionError("Unexpected protection module state");
                out.println("PASS addon discovery; protection=" + protection);
                Object server = event.getClass().getMethod("getServer").invoke(event);
                Object level = server.getClass().getMethod("overworld").invoke(server);
                Class<?> builtins = Class.forName("net.minecraft.core.registries.BuiltInRegistries");
                Class<?> registry = Class.forName("net.minecraft.core.Registry");
                Class<?> resource = Class.forName("net.minecraft.resources.ResourceLocation");
                Class<?> block = Class.forName("net.minecraft.world.level.block.Block");
                Class<?> state = Class.forName("net.minecraft.world.level.block.state.BlockState");
                Class<?> posType = Class.forName("net.minecraft.core.BlockPos");
                Class<?> reader = Class.forName("net.minecraft.world.level.LevelReader");
                Object blocks = builtins.getField("BLOCK").get(null);
                Method parse = resource.getMethod("parse", String.class);
                Method get = registry.getMethod("get", resource);
                Method key = singleMethod(registry, "getKey", 1);
                Method defaultState = block.getMethod("defaultBlockState");
                Method map = Class.forName("net.pixelbank.burnt.compat.BurnMappingRegistry").getMethod("get", block);
                Object position = posType.getConstructor(int.class, int.class, int.class).newInstance(0, 65, 0);
                Method corrupt = Class.forName("com.yayuy.overgrownvegetation.corruption.CorruptionRegistry").getMethod("canCorrupt", reader, posType, state);

                int mappings = 0;
                for (JsonElement entry : expected.getAsJsonArray("mappings")) {
                    JsonObject e = entry.getAsJsonObject();
                    String from = e.get("from").getAsString(), to = e.get("to").getAsString();
                    Object source = get.invoke(blocks, parse.invoke(null, from));
                    Object mapped = map.invoke(null, source);
                    String actual = mapped == null ? "null" : key.invoke(blocks, mapped).toString();
                    if (!to.equals(actual)) throw new AssertionError("Mapping " + from + " expected " + to + " got " + actual);
                    mappings++;
                }
                out.println("PASS explicit Burnt mappings: " + mappings);

                Class<?> tagType = Class.forName("net.minecraft.tags.TagKey");
                Class<?> resourceKey = Class.forName("net.minecraft.resources.ResourceKey");
                Object blockKey = Class.forName("net.minecraft.core.registries.Registries").getField("BLOCK").get(null);
                Object immuneTag = tagType.getMethod("create", resourceKey, resource).invoke(null, blockKey, parse.invoke(null, "overgrown_vegetation:corruption_immune"));
                Method isTag = state.getMethod("is", tagType);
                int protectedCount = 0;
                int naturallyInfectable = 0;
                for (JsonElement value : expected.getAsJsonArray("immune_blocks")) {
                    Object b = get.invoke(blocks, parse.invoke(null, value.getAsString()));
                    if (!value.getAsString().equals(key.invoke(blocks, b).toString())) throw new AssertionError("Missing block " + value);
                    boolean tagged = (boolean) isTag.invoke(defaultState.invoke(b), immuneTag);
                    if (tagged != protection) throw new AssertionError("Unexpected immunity tag for " + value);
                    boolean can = (boolean) corrupt.invoke(null, level, position, defaultState.invoke(b));
                    if (protection && can) throw new AssertionError("Protected remnant still corruptible: " + value);
                    if (!protection && can) naturallyInfectable++;
                    if (!protection && value.getAsString().equals("burnt:burnt_dirt") && !can) throw new AssertionError("Core-only unexpectedly protects burnt dirt");
                    protectedCount++;
                }
                out.println("PASS immunity tag membership for all Burnt remnants: " + protectedCount + "; protection=" + protection);
                if (protection) out.println("PASS actual canCorrupt rejects all protected remnants: " + protectedCount);
                else out.println("PASS unmodified Overgrown corruption eligibility: " + naturallyInfectable + " of " + protectedCount + " remnants naturally infectable; burnt dirt infectable");

                Object grass = get.invoke(blocks, parse.invoke(null, "minecraft:grass_block"));
                if (!(boolean) corrupt.invoke(null, level, position, defaultState.invoke(grass))) throw new AssertionError("Normal grass unexpectedly immune");
                out.println("PASS normal grass remains infectable");

                Object destroy = tagType.getMethod("create", resourceKey, resource).invoke(null, blockKey, parse.invoke(null, "burnt:destroy_in_burn"));
                int tagCount = 0;
                for (var group : expected.getAsJsonObject("groups").entrySet()) {
                    Object tag = tagType.getMethod("create", resourceKey, resource).invoke(null, blockKey, parse.invoke(null, "burnt:" + group.getKey()));
                    for (JsonElement value : group.getValue().getAsJsonArray()) {
                        Object b = get.invoke(blocks, parse.invoke(null, "overgrown_vegetation:" + value.getAsString()));
                        if (!key.invoke(blocks, b).toString().equals("overgrown_vegetation:" + value.getAsString())) throw new AssertionError("Missing source block " + value);
                        if (!(boolean) isTag.invoke(defaultState.invoke(b), tag)) throw new AssertionError("Missing tag " + group.getKey() + " for " + value);
                        tagCount++;
                    }
                }
                out.println("PASS Burnt category tags for all source blocks: " + tagCount);
                int destroyed = 0;
                for (JsonElement e : expected.getAsJsonObject("groups").getAsJsonArray("destroy_in_burn")) {
                    Object b = get.invoke(blocks, parse.invoke(null, "overgrown_vegetation:" + e.getAsString()));
                    if (!(boolean) isTag.invoke(defaultState.invoke(b), destroy)) throw new AssertionError("Missing burn-removal tag " + e);
                    destroyed++;
                }
                out.println("PASS vines and corpses in burn-removal tag: " + destroyed);

                Object entities = builtins.getField("ENTITY_TYPE").get(null);
                Class<?> entityType = Class.forName("net.minecraft.world.entity.EntityType");
                for (String id : new String[]{"overgrown_vegetation:hive_node", "overgrown_vegetation:overgrown_nexus"}) {
                    Object entity = get.invoke(entities, parse.invoke(null, id));
                    if (!(boolean) entityType.getMethod("fireImmune").invoke(entity)) throw new AssertionError("Original fire immunity changed: " + id);
                }
                out.println("PASS central enemies retain original fire immunity");
                out.println("RESULT PASS");
                System.out.println("FIREBREAKS_VERIFICATION PASS");
            } catch (Throwable error) {
                out.println("RESULT FAIL");
                error.printStackTrace(out);
                System.out.println("FIREBREAKS_VERIFICATION FAIL: " + error);
            }
        } catch (IOException error) {
            error.printStackTrace();
        }
    }
}
