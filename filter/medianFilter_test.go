package main

import (
	"fmt"
	"os"
	"testing"
)

// Benchmark applies the filter to the ship.png b.N times.
// The time taken is carefully measured by go.
// The b.N  repetition is needed because benchmark results are not always constant.
func BenchmarkFilter(b *testing.B) {
	// Disable all program output apart from benchmark results
	os.Stdout = nil 

	// Use a for-loop to run 5 sub-benchmarks, with 1, 2, 4, 8 and 16 workers.
	for threads := 1; threads <= 16; threads*=2 {
		b.Run(fmt.Sprintf("%d_workers", threads), func(b *testing.B) {
			for i := 0; i < b.N; i++ {
				filter("ship.png", fmt.Sprintf("out_%d.png", threads), threads)
			}
		})
	}
}
