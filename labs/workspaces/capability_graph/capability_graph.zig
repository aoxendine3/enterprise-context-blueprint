// workspaces/capability_graph/capability_graph.zig
// Xoras Capability Graph — idiomatic Zig 0.16
// Nodes represent assets, edges represent signed proofs of dependency with timestamps.
// Provides O(1) supersededBy lookup via an index map.

const std = @import("std");

pub const NodeId = u32;

pub const EdgeInfo = struct {
    signed_proof: [64]u8,
    timestamp: i64,
    from: NodeId,
    to: NodeId,
};

pub const Graph = struct {
    allocator: std.mem.Allocator,
    // adjacency list of outgoing edges per node
    adj: std.AutoHashMap(NodeId, std.ArrayList(EdgeInfo)),
    // reverse lookup: node -> superseding node (the node that supersedes it)
    superseded_by: std.AutoHashMap(NodeId, EdgeInfo),
    // set of all nodes for iteration
    nodes: std.AutoHashMap(NodeId, void),

    pub fn init(allocator: std.mem.Allocator) Graph {
        return Graph{
            .allocator = allocator,
            .adj = std.AutoHashMap(NodeId, std.ArrayList(EdgeInfo)).init(allocator),
            .superseded_by = std.AutoHashMap(NodeId, EdgeInfo).init(allocator),
            .nodes = std.AutoHashMap(NodeId, void).init(allocator),
        };
    }

    pub fn deinit(self: *Graph) void {
        var it = self.adj.iterator();
        while (it.next()) |entry| {
            entry.value_ptr.deinit(self.allocator);
        }
        self.adj.deinit();
        self.superseded_by.deinit();
        self.nodes.deinit();
    }

    pub fn addNode(self: *Graph, id: NodeId) !void {
        try self.nodes.put(id, {});
        if (!self.adj.contains(id)) {
            try self.adj.put(id, .empty);
        }
    }

    // Add an edge with signed proof and timestamp.
    pub fn addEdge(self: *Graph, from: NodeId, to: NodeId, proof: [64]u8, ts: i64) !void {
        try self.addNode(from);
        try self.addNode(to);
        const edge = EdgeInfo{ .signed_proof = proof, .timestamp = ts, .from = from, .to = to };
        const list = self.adj.getPtr(from) orelse return error.MissingNode;
        try list.append(self.allocator, edge);
        // For supersession each node is superseded by the incoming edge
        try self.superseded_by.put(to, edge);
    }

    // O(1) lookup of superseding node and provenance.
    pub fn supersededBy(self: *Graph, id: NodeId) ?EdgeInfo {
        return self.superseded_by.get(id);
    }

    // Detect cycles via DFS. Returns true if a cycle exists.
    pub fn hasCycle(self: *Graph) bool {
        var visited = std.AutoHashMap(NodeId, void).init(self.allocator);
        var stack = std.AutoHashMap(NodeId, void).init(self.allocator);
        defer visited.deinit();
        defer stack.deinit();
        var node_it = self.nodes.iterator();
        while (node_it.next()) |kv| {
            if (self.dfsDetect(kv.key_ptr.*, &visited, &stack)) return true;
        }
        return false;
    }

    fn dfsDetect(self: *Graph, id: NodeId, visited: *std.AutoHashMap(NodeId, void), stack: *std.AutoHashMap(NodeId, void)) bool {
        if (stack.contains(id)) return true; // back edge -> cycle
        if (visited.contains(id)) return false;
        visited.put(id, {}) catch return false;
        stack.put(id, {}) catch return false;
        const edges = self.adj.get(id) orelse return false;
        for (edges.items) |e| {
            if (self.dfsDetect(e.to, visited, stack)) return true;
        }
        _ = stack.remove(id);
        return false;
    }

    // Topological order of DAG (fails on cycle).
    pub fn topologicalSort(self: *Graph, allocator: std.mem.Allocator) !std.ArrayList(NodeId) {
        if (self.hasCycle()) return error.CycleDetected;
        var indegree = std.AutoHashMap(NodeId, usize).init(allocator);
        defer indegree.deinit();

        var node_it = self.nodes.iterator();
        while (node_it.next()) |kv| {
            try indegree.put(kv.key_ptr.*, 0);
        }

        var adj_it = self.adj.iterator();
        while (adj_it.next()) |kv| {
            for (kv.value_ptr.items) |e| {
                const cur = indegree.get(e.to) orelse return error.MissingNode;
                try indegree.put(e.to, cur + 1);
            }
        }

        var queue: std.ArrayList(NodeId) = .empty;
        defer queue.deinit(allocator);

        var indeg_it = indegree.iterator();
        while (indeg_it.next()) |kv| {
            if (kv.value_ptr.* == 0) try queue.append(allocator, kv.key_ptr.*);
        }

        var result: std.ArrayList(NodeId) = .empty;
        errdefer result.deinit(allocator);

        while (queue.pop()) |n| {
            try result.append(allocator, n);
            const out_edges = self.adj.getPtr(n) orelse continue;
            for (out_edges.items) |e| {
                const cur = indegree.get(e.to) orelse return error.MissingNode;
                const new = cur - 1;
                try indegree.put(e.to, new);
                if (new == 0) try queue.append(allocator, e.to);
            }
        }
        if (result.items.len != self.nodes.count()) return error.CycleDetected;
        return result;
    }
};

// Tests
test "superseded_by_returns_provenance" {
    const alloc = std.testing.allocator;
    var g = Graph.init(alloc);
    defer g.deinit();
    const id1: NodeId = 1;
    const id2: NodeId = 2;
    var proof: [64]u8 = undefined;
    @memset(&proof, 0xAA);
    try g.addEdge(id1, id2, proof, 1234567890);
    const edge = g.supersededBy(id2) orelse return error.TestFailed;
    try std.testing.expect(edge.from == id1);
    try std.testing.expect(edge.timestamp == 1234567890);
    try std.testing.expect(std.mem.eql(u8, &edge.signed_proof, &proof));
}

test "cycle_detection" {
    const alloc = std.testing.allocator;
    var g = Graph.init(alloc);
    defer g.deinit();
    var p: [64]u8 = undefined;
    @memset(&p, 0xFF);
    try g.addEdge(1, 2, p, 1);
    try g.addEdge(2, 3, p, 2);
    try g.addEdge(3, 1, p, 3);
    try std.testing.expect(g.hasCycle());
}

test "topo_order_dag" {
    const alloc = std.testing.allocator;
    var g = Graph.init(alloc);
    defer g.deinit();
    var p: [64]u8 = undefined;
    @memset(&p, 0x01);
    try g.addEdge(1, 2, p, 1);
    try g.addEdge(1, 3, p, 2);
    try g.addEdge(2, 4, p, 3);
    try g.addEdge(3, 4, p, 4);
    var order = try g.topologicalSort(alloc);
    defer order.deinit(alloc);

    var pos = std.AutoHashMap(NodeId, usize).init(alloc);
    defer pos.deinit();
    for (order.items, 0..) |id, idx| {
        try pos.put(id, idx);
    }
    try std.testing.expect(pos.get(1).? < pos.get(2).?);
    try std.testing.expect(pos.get(1).? < pos.get(3).?);
    try std.testing.expect(pos.get(2).? < pos.get(4).?);
    try std.testing.expect(pos.get(3).? < pos.get(4).?);
}
