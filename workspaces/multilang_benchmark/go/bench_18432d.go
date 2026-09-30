// Calibrated Go 1.22 18,432-D Hexological Vector Engine Benchmark
// Substrate: Apple Silicon M4 Bare Metal (10 CPU Cores / Goroutines)

package main

import (
	"encoding/json"
	"fmt"
	"sort"
	"sync"
	"sync/atomic"
	"time"
)

const (
	DIM           = 18432
	TOTAL_VECTORS = 100000
	NUM_CORES     = 10
	ITERATIONS    = 50
)

var gVolatileSink uint64

type BenchmarkResult struct {
	Language       string  `json:"language"`
	AvgPassMs      float64 `json:"avg_pass_ms"`
	EvalsPerSec    float64 `json:"evals_per_sec"`
	Gflops         float64 `json:"gflops"`
	BandwidthGbSec float64 `json:"bandwidth_gb_sec"`
	P50Us          float64 `json:"p50_us"`
	P90Us          float64 `json:"p90_us"`
	P99Us          float64 `json:"p99_us"`
	SinkCheck      uint64  `json:"sink_check"`
}

func go18432dDotProduct(a, b []float32) float32 {
	var sum0, sum1, sum2, sum3 float32
	for i := 0; i < DIM; i += 4 {
		sum0 += a[i] * b[i]
		sum1 += a[i+1] * b[i+1]
		sum2 += a[i+2] * b[i+2]
		sum3 += a[i+3] * b[i+3]
	}
	return sum0 + sum1 + sum2 + sum3
}

func main() {
	query := make([]float32, DIM)
	for i := 0; i < DIM; i++ {
		query[i] = float32(i%100) * 0.001
	}

	matrix := make([]float32, TOTAL_VECTORS*DIM)
	for i := 0; i < TOTAL_VECTORS*DIM; i++ {
		matrix[i] = float32((i+1)%100) * 0.001
	}

	vecsPerCore := TOTAL_VECTORS / NUM_CORES

	// 1. Warmup Pass (2 passes for Go)
	for warm := 0; warm < 2; warm++ {
		var wg sync.WaitGroup
		for t := 0; t < NUM_CORES; t++ {
			wg.Add(1)
			startIdx := t * vecsPerCore
			count := vecsPerCore
			if t == NUM_CORES-1 {
				count = TOTAL_VECTORS - startIdx
			}
			go func(sIdx, cnt int) {
				defer wg.Done()
				var localSum float32
				for i := 0; i < cnt; i++ {
					vecIdx := sIdx + i
					target := matrix[vecIdx*DIM : (vecIdx+1)*DIM]
					localSum += go18432dDotProduct(query, target)
				}
				atomic.AddUint64(&gVolatileSink, uint64(localSum))
			}(startIdx, count)
		}
		wg.Wait()
	}

	// 2. Timed Iterations
	sampleLatenciesMs := make([]float64, 0, ITERATIONS)
	tStartAll := time.Now()

	for iter := 0; iter < ITERATIONS; iter++ {
		iterStart := time.Now()
		var wg sync.WaitGroup
		for t := 0; t < NUM_CORES; t++ {
			wg.Add(1)
			startIdx := t * vecsPerCore
			count := vecsPerCore
			if t == NUM_CORES-1 {
				count = TOTAL_VECTORS - startIdx
			}
			go func(sIdx, cnt int) {
				defer wg.Done()
				var localSum float32
				for i := 0; i < cnt; i++ {
					vecIdx := sIdx + i
					target := matrix[vecIdx*DIM : (vecIdx+1)*DIM]
					localSum += go18432dDotProduct(query, target)
				}
				atomic.AddUint64(&gVolatileSink, uint64(localSum))
			}(startIdx, count)
		}
		wg.Wait()
		iterMs := float64(time.Since(iterStart).Milliseconds())
		sampleLatenciesMs = append(sampleLatenciesMs, iterMs)
	}

	totalElapsedSec := time.Since(tStartAll).Seconds()
	avgPassSec := totalElapsedSec / float64(ITERATIONS)
	avgPassMs := avgPassSec * 1000.0

	evalsPerSec := float64(TOTAL_VECTORS) / avgPassSec
	gflops := (float64(TOTAL_VECTORS) * float64(DIM) * 2.0) / (avgPassSec * 1e9)
	bytesGb := (float64(TOTAL_VECTORS) * float64(DIM) * 4.0) / (1024.0 * 1024.0 * 1024.0)
	bandwidthGbSec := bytesGb / avgPassSec

	sort.Float64s(sampleLatenciesMs)
	n := float64(len(sampleLatenciesMs))
	p50PassMs := sampleLatenciesMs[int(n*0.50)]
	p90PassMs := sampleLatenciesMs[int(n*0.90)]
	p99PassMs := sampleLatenciesMs[int(n*0.99)]

	p50VecUs := (p50PassMs * 1000.0) / float64(TOTAL_VECTORS)
	p90VecUs := (p90PassMs * 1000.0) / float64(TOTAL_VECTORS)
	p99VecUs := (p99PassMs * 1000.0) / float64(TOTAL_VECTORS)

	res := BenchmarkResult{
		Language:       "Go 1.22 (go build)",
		AvgPassMs:      avgPassMs,
		EvalsPerSec:    evalsPerSec,
		Gflops:         gflops,
		BandwidthGbSec: bandwidthGbSec,
		P50Us:          p50VecUs,
		P90Us:          p90VecUs,
		P99Us:          p99VecUs,
		SinkCheck:      atomic.LoadUint64(&gVolatileSink),
	}

	out, _ := json.MarshalIndent(res, "", "  ")
	fmt.Println(string(out))
}
