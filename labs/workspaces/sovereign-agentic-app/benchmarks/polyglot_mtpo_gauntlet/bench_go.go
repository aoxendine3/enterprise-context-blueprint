package main

import (
	"encoding/json"
	"fmt"
	"runtime"
	"sync"
	"sync/atomic"
	"time"
)

const (
	HexCellSlots = 6
	TotalOps     = 1000000
	NumThreads   = 8
	OpsPerThread = TotalOps / NumThreads
)

type AlignedSlot struct {
	_      [56]byte
	active uint64
	_      [56]byte
	shadow uint64
}

type HexCellRing struct {
	slots            [HexCellSlots]AlignedSlot
	totalCommitted   uint64
	totalCompensated uint64
}

func (r *HexCellRing) executeSaga(slot int, txID uint64, newVal uint64) bool {
	initial := atomic.LoadUint64(&r.slots[slot].active)
	atomic.StoreUint64(&r.slots[slot].shadow, newVal)

	if atomic.CompareAndSwapUint64(&r.slots[slot].active, initial, newVal) {
		atomic.AddUint64(&r.totalCommitted, 1)
		return true
	} else {
		atomic.StoreUint64(&r.slots[slot].shadow, initial)
		atomic.AddUint64(&r.totalCompensated, 1)
		return false
	}
}

func main() {
	runtime.GOMAXPROCS(NumThreads)
	var ring HexCellRing

	var wg sync.WaitGroup
	wg.Add(NumThreads)

	start := time.Now()

	var totalRetries uint64

	for tid := 0; tid < NumThreads; tid++ {
		go func(threadID int) {
			defer wg.Done()
			startTx := uint64(threadID*OpsPerThread + 1)
			var localRetries uint64

			for i := uint64(0); i < OpsPerThread; i++ {
				txID := startTx + i
				slot := int(txID % HexCellSlots)
				newVal := uint64(0xBEAF000000000000) | txID

				for !ring.executeSaga(slot, txID, newVal) {
					localRetries++
				}
			}
			atomic.AddUint64(&totalRetries, localRetries)
		}(tid)
	}

	wg.Wait()
	elapsed := time.Since(start)

	var mem runtime.MemStats
	runtime.ReadMemStats(&mem)
	rssMB := float64(mem.Sys) / (1024.0 * 1024.0)

	elapsedSec := elapsed.Seconds()
	opsSec := float64(TotalOps) / elapsedSec
	avgLatencyNs := (elapsedSec / float64(TotalOps)) * 1e9

	out := map[string]interface{}{
		"language":           "Go 1.26 (sync/atomic goroutines)",
		"standard":           "CSP + Go Runtime Scheduler",
		"total_ops":          TotalOps,
		"threads":            NumThreads,
		"elapsed_ms":         elapsed.Milliseconds(),
		"throughput_ops_sec": int(opsSec),
		"avg_latency_ns":     avgLatencyNs,
		"total_committed":    atomic.LoadUint64(&ring.totalCommitted),
		"contention_retries": atomic.LoadUint64(&totalRetries),
		"peak_rss_mb":        rssMB,
	}

	b, _ := json.MarshalIndent(out, "", "  ")
	fmt.Println(string(b))
}
