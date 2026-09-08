package main

import "fmt"

//go:noinline
func bench(n int) int {
	x := 0
	for i := 0; i < n; i++ {
		x += i
	}
	return x
}

func main() {
	fmt.Println("ego enclave: single-step target running")
	fmt.Println(bench(100))
}
