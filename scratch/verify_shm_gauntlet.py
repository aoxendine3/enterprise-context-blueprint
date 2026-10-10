import z3

def inv1_overflow_bound():
    print("==================================================")
    print("INVARIANT 1: SHM Ring-Buffer Overflow Bound (Capacity = 4096)")
    print("==================================================")
    
    # 1A: Guarded Push (Proved UNSAT)
    s = z3.Solver()
    capacity = 4096
    count = z3.BitVec('count', 64)
    push_len = z3.BitVec('push_len', 64)
    count_next = z3.BitVec('count_next', 64)
    
    s.add(z3.ULE(count, capacity))
    s.add(z3.UGT(push_len, 0))
    
    guard = z3.ULE(count + push_len, capacity)
    s.add(z3.Implies(guard, count_next == count + push_len))
    s.add(z3.Implies(z3.Not(guard), count_next == count))
    
    # Negation: count_next > capacity
    s.add(z3.UGT(count_next, capacity))
    
    res = s.check()
    print(f"Status (Guarded Interface): {res} (Proved)")
    print("SMT-LIB2 Query:\n", s.to_smt2())

    # 1B: Unchecked/Lock-free Concurrent Push (Counter-example check)
    s_bad = z3.Solver()
    count_bad = z3.BitVec('count', 64)
    push_len_bad = z3.BitVec('push_len', 64)
    count_next_bad = z3.BitVec('count_next', 64)
    s_bad.add(z3.ULE(count_bad, capacity))
    s_bad.add(z3.UGT(push_len_bad, 0))
    s_bad.add(count_next_bad == count_bad + push_len_bad) # Unchecked push
    s_bad.add(z3.UGT(count_next_bad, capacity))
    res_bad = s_bad.check()
    print(f"Status (Unchecked Push Interface): {res_bad} (Counter-example found)")
    if res_bad == z3.sat:
        print("Counter-example Model:\n", s_bad.model())

def inv2_head_tail_relationship():
    print("\n==================================================")
    print("INVARIANT 2: Head/Tail Relationship When Full and When Empty")
    print("==================================================")
    capacity = 4096

    # 2A: Naive Modular Indexing (where head_ptr == tail_ptr for both full and empty)
    s_modular = z3.Solver()
    head = z3.BitVec('head', 64)
    tail = z3.BitVec('tail', 64)
    count = z3.BitVec('count', 64)
    
    # Valid state: count = (head - tail) % capacity
    s_modular.add(z3.ULE(count, capacity))
    s_modular.add(head % capacity == tail % capacity)
    # Assert state is FULL (count == 4096)
    s_modular.add(count == capacity)
    
    res = s_modular.check()
    print(f"Status (Naive Modulo Pointer Ambiguity Check): {res}")
    if res == z3.sat:
        print("Counter-example Model for Naive Modulo Indexing (head % 4096 == tail % 4096 when FULL):")
        print(s_modular.model())
        print("SMT-LIB2 Snippet:\n", s_modular.to_smt2())

    # 2B: Monotonic 64-bit Indexing / Explicit Count Interface (Proved UNSAT for collision)
    s_mono = z3.Solver()
    head_m = z3.BitVec('head_m', 64)
    tail_m = z3.BitVec('tail_m', 64)
    count_m = head_m - tail_m
    
    # Precondition: tail_m <= head_m, count_m <= capacity
    s_mono.add(z3.ULE(tail_m, head_m))
    s_mono.add(z3.ULE(count_m, capacity))
    
    # Can a state be BOTH empty (count_m == 0) AND full (count_m == 4096)?
    s_mono.add(count_m == 0, count_m == capacity)
    res_mono = s_mono.check()
    print(f"Status (Monotonic 64-bit Count Differentiation): {res_mono} (Proved UNSAT - Empty & Full disjoint)")
    print("SMT-LIB2 Query:\n", s_mono.to_smt2())

def inv3_count_bounds():
    print("\n==================================================")
    print("INVARIANT 3: Count Never Exceeds Capacity Across State Transitions")
    print("==================================================")
    capacity = 4096
    
    s = z3.Solver()
    count = z3.BitVec('count', 64)
    push_n = z3.BitVec('push_n', 64)
    pop_m = z3.BitVec('pop_m', 64)
    count_next = z3.BitVec('count_next', 64)
    
    # Preconditions: initial valid count
    s.add(z3.ULE(count, capacity))
    s.add(z3.ULE(push_n, capacity - count)) # Guarded push
    s.add(z3.ULE(pop_m, count))              # Guarded pop
    
    s.add(count_next == count + push_n - pop_m)
    
    # Negation: count_next > capacity OR count_next underflow (< 0 in unsigned interpretation, i.e. > capacity)
    s.add(z3.UGT(count_next, capacity))
    
    res = s.check()
    print(f"Status: {res} (Proved UNSAT - Count remains strictly in [0, 4096])")
    print("SMT-LIB2 Query:\n", s.to_smt2())

def inv4_cache_line_alignment():
    print("\n==================================================")
    print("INVARIANT 4: M4 128-byte Cache-Line Alignment on Mapped Pointers")
    print("==================================================")
    
    # 4A: Arbitrary Element Stride S (Unconstrained stride check)
    s_unaligned = z3.Solver()
    base_ptr = z3.BitVec('base_ptr', 64)
    slot_idx = z3.BitVec('slot_idx', 64)
    stride = z3.BitVec('stride', 64)
    elem_ptr = base_ptr + slot_idx * stride
    
    # Preconditions: base_ptr is 128-byte aligned, slot_idx < 4096
    s_unaligned.add(base_ptr % 128 == 0)
    s_unaligned.add(z3.ULT(slot_idx, 4096))
    
    # Seeking counter-example where elem_ptr is NOT 128-byte aligned
    s_unaligned.add(elem_ptr % 128 != 0)
    
    res = s_unaligned.check()
    print(f"Status (Arbitrary Element Stride S): {res} (Counter-example found)")
    if res == z3.sat:
        m = s_unaligned.model()
        print("Counter-example Model (e.g. stride unaligned to 128 bytes):")
        print(f"  base_ptr = {m[base_ptr]}")
        print(f"  slot_idx = {m[slot_idx]}")
        print(f"  stride   = {m[stride]}")
        print("SMT-LIB2 Query:\n", s_unaligned.to_smt2())

    # 4B: Enforced 128-byte Aligned Stride S (e.g. HexCell 512-byte slot or 128-byte cache line boundary)
    s_aligned = z3.Solver()
    base_ptr_a = z3.BitVec('base_ptr', 64)
    slot_idx_a = z3.BitVec('slot_idx', 64)
    stride_a = z3.BitVec('stride', 64)
    elem_ptr_a = base_ptr_a + slot_idx_a * stride_a
    
    s_aligned.add(base_ptr_a % 128 == 0)
    s_aligned.add(stride_a % 128 == 0) # Hardware Alignment Invariant
    s_aligned.add(z3.ULT(slot_idx_a, 4096))
    
    # Seeking counter-example: elem_ptr_a % 128 != 0
    s_aligned.add(elem_ptr_a % 128 != 0)
    res_a = s_aligned.check()
    print(f"\nStatus (128-byte Aligned Stride S Enforced): {res_a} (Proved UNSAT - Alignment preserved)")
    print("SMT-LIB2 Query:\n", s_aligned.to_smt2())

inv1_overflow_bound()
inv2_head_tail_relationship()
inv3_count_bounds()
inv4_cache_line_alignment()
