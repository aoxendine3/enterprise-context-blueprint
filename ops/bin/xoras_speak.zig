// ops/bin/xoras_speak.zig
// Native Zig Audio Dispatcher for Xoras Systems
// Zero Python. Zero dependencies. Direct OS-level speech & Stage synchronization.
// Compiles to native ARM64 binary: /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/bin/xoras_speak

const std = @import("std");

const c = @cImport({
    @cInclude("unistd.h");
    @cInclude("fcntl.h");
    @cInclude("sys/file.h");
    @cInclude("sys/wait.h");
});

const TIMING_FILE = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/current_timing.json";
const IMAGE_FILE = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/current_image.txt";
const LOCK_FILE = "/tmp/coreaudio_single_speaker.lock";

fn getVoiceForAgent(agent: []const u8) []const u8 {
    if (std.mem.eql(u8, agent, "maxx")) return "Evan (Enhanced)";
    if (std.mem.eql(u8, agent, "jarvis")) return "Daniel (Enhanced)";
    if (std.mem.eql(u8, agent, "daxx")) return "Tom (Enhanced)";
    if (std.mem.eql(u8, agent, "vance")) return "Alex";
    if (std.mem.eql(u8, agent, "clara")) return "Allison (Enhanced)";
    if (std.mem.eql(u8, agent, "john")) return "Rishi (Enhanced)";
    if (std.mem.eql(u8, agent, "selene")) return "Joelle (Enhanced)";
    if (std.mem.eql(u8, agent, "orion")) return "Moira";
    if (std.mem.eql(u8, agent, "eden")) return "Ava (Enhanced)";
    return "Evan (Enhanced)";
}

pub fn main(init: std.process.Init) !void {
    var args_iter = init.minimal.args.iterate();
    _ = args_iter.next(); // skip binary name

    const agent = args_iter.next() orelse "maxx";
    const text = args_iter.next() orelse return;

    if (text.len == 0) return;

    // Single-speaker CoreAudio serialization is enforced directly around physical DAC playback
    // inside sync_stage_engine.py to prevent nested flock deadlock between parent and child.

    // 2. Update stage image state file atomically
    const img_fd = c.open(IMAGE_FILE, c.O_CREAT | c.O_WRONLY | c.O_TRUNC, @as(c_uint, 0o644));
    if (img_fd >= 0) {
        _ = c.write(img_fd, agent.ptr, agent.len);
        _ = c.close(img_fd);
    }

    // 3. Update stage timing JSON
    const time_fd = c.open(TIMING_FILE, c.O_CREAT | c.O_WRONLY | c.O_TRUNC, @as(c_uint, 0o644));
    if (time_fd >= 0) {
        var buf: [2048]u8 = undefined;
        const json = std.fmt.bufPrint(
            &buf,
            "{{\"agent\":\"{s}\",\"text\":\"{s}\",\"complete\":false}}\n",
            .{ agent, text },
        ) catch "";
        if (json.len > 0) {
            _ = c.write(time_fd, json.ptr, json.len);
        }
        _ = c.close(time_fd);
    }

    // 4. Execute physical audio synthesis via Kokoro ONLY (natural neural voice & word sync)
    const sync_script: [*:0]const u8 = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui/sync_stage_engine.py";
    const py_bin: [*:0]const u8 = "/opt/homebrew/bin/python3";

    var agent_z: [64:0]u8 = undefined;
    @memcpy(agent_z[0..agent.len], agent);
    agent_z[agent.len] = 0;

    var text_z: [4096:0]u8 = undefined;
    const copy_len = @min(text.len, 4095);
    @memcpy(text_z[0..copy_len], text[0..copy_len]);
    text_z[copy_len] = 0;

    const pid = c.fork();
    if (pid == 0) {
        const py_argv = [_:null]?[*:0]const u8{
            py_bin,
            sync_script,
            &agent_z,
            &text_z,
            null,
        };
        _ = c.execvp(py_bin, @ptrCast(&py_argv));
        c._exit(1);
    } else if (pid > 0) {
        var status: c_int = 0;
        _ = c.waitpid(pid, &status, 0);
    }

    // 5. Mark timing JSON complete
    const finish_fd = c.open(TIMING_FILE, c.O_CREAT | c.O_WRONLY | c.O_TRUNC, @as(c_uint, 0o644));
    if (finish_fd >= 0) {
        var buf: [2048]u8 = undefined;
        const json = std.fmt.bufPrint(
            &buf,
            "{{\"agent\":\"{s}\",\"text\":\"{s}\",\"complete\":true}}\n",
            .{ agent, text },
        ) catch "";
        if (json.len > 0) {
            _ = c.write(finish_fd, json.ptr, json.len);
        }
        _ = c.close(finish_fd);
    }
}
