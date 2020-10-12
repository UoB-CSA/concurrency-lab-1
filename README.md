# Concurrency Lab 1

> If you're stuck look at examples on [Go by Example](https://gobyexample.com/)

## Using the lab sheet

There are two ways to use the lab sheet, you can either:

- [create a new repo from this template](https://github.com/UoB-CSA/concurrency-lab-1/generate) - **this is the recommended way**
- download a [zip file](https://github.com/UoB-CSA/concurrency-lab-1/archive/master.zip)

Each question is rated to help you balance your work:

- :red_circle::white_circle::white_circle::white_circle::white_circle: - Easy, strictly necessary.
- :red_circle::red_circle::white_circle::white_circle::white_circle: - Medium, still necessary.
- :red_circle::red_circle::red_circle::white_circle::white_circle: - Hard, necessary if you're aiming for higher marks.
- :red_circle::red_circle::red_circle::red_circle::white_circle: - Hard, useful for coursework extensions.
- :red_circle::red_circle::red_circle::red_circle::red_circle: - Hard, beyond what you need for any part of the coursework.

## Question 1 - Median Filter :red_circle::red_circle::white_circle::white_circle::white_circle:

Open the images in the `filter` directory. As you can see, they all have 'salt and pepper' noise. Now open `medianFilter.go`. It's a single-threaded implementation of a Median Filter, which removes the salt and pepper noise. It runs through the image pixel by pixel and replaces each value with the median of neighbouring values. In this implementation, the algorithm has hardcoded radius 2 and therefore it looks at 24 neighbours (as well as its own value).

### Question 1a

```bash
Usage of ./medianFilter:
  -in string
        Specify the input file. (default "ship.png")
  -out string
        Specify the output file. (default "out.png")
```

Read the source code, run the filter on the provided images and verify that the noise has been removed.

Make sure you run this program using either `go build` or `go run`. IDE autorun tools may not read the image files correctly.

### Question 1b

The median filter is an example of a problem that is "embarrassingly parallelisable". Consider having 4 worker threads. We could split the image into 4 parts and ask each worker to process their chunk in parallel to other workers. At the end, we can collect the result and output the final image.

#### Sending

The first problem we encounter when parallelising is how to send the workers their respective chunks of the image:

We *could* use channels of type `chan [][]uint8` to send parts of the image to the worker as pure 2D slices. For example using the notation `image[0:128]`. This is not a good solution. Recall from lab 1 that passing a slice to a function simply passes a pointer. If we passed the same slice to multiple workers we could end up concurrently modifying the slice causing an incorrect resulting image.

We *could* use channels of type `chan uint8` to pass `uint8` values one by one, rather than slices. While this is a valid and safe solution, it isn't particularly fast.

Instead, today we will explore how to create a *closure* that will make our slice immutable.

The variable `immutableData` in the function `filter()` is a closure. It is **not** a slice or any other data type. The function `makeImmutableMatrix(...)` returns a function. It stores a reference to a 2D slice and given `y` and `x` coordinates it returns a `uint8` from that slice that it wraps - it is similar to an object with a getter in java. Such a function with hidden state is called a [closure](https://gobyexample.com/closures).

The use of a closure means that the slice it wraps effectively becomes immutable. As a programmer, you now have no direct access to the pointer and therefore no way of modifying the slice. This will allow us to pass the closure to multiple goroutines without causing any potential [race conditions](https://en.wikipedia.org/wiki/Race_condition) since concurrent read operations are perfectly safe - concurrent writes or reads when a write may be happening almost always aren't.

#### Receiving

The second problem is receiving and reconstructing the image back in the function `filter()`:

We *could* use channels of type `chan uint8` to pass `uint8` values one by one. While this is a valid and safe solution, it isn't particularly fast.

We *could* use a channel of type `chan func(y, x int) uint8` to send back a closure. However, to put together the final image in a single 2D slice we will need to use `append`, which is not supported by a closure. We would, therefore, end up extracting the `uint8` values one by one which is slow.

Our solution will use a channel of type `chan [][]uint8` to send the resulting image back to `filter()`. We will send a slice (~pointer) over a channel, but in this case, there are no race conditions, because the worker exits immediately after sending the slice. This does not invalidate the memory (like it could in C). As a result, the slice will only be owned by a single goroutine (the `filter()` one) and there will be no race conditions.

#### Task

Start parallelising the median filter by creating a `worker(...)` function. Given a closure and some y and x bounds it should apply the median filter between these bounds and 'return' the newly created slice.

<details>
    <summary>Hint 1</summary>

The signature of the worker function could be:

```go
func worker(startY, endY, startX, endX int, data func(y, x int) uint8, out chan<- [][]uint8) {

}
```

</details>

<details>
    <summary>Hint 2</summary>

You only need two lines of code in the worker. One to execute the median filter and one to send the resulting slice back on the `out` channel.

</details>

### Question 1c

Now that we've created a worker we need to change how `filter()` works. It needs to distribute the image between 4 workers, wait for them to finish, and then reconstruct the image in a single 2D slice so that it can be saved to a file.

Instead of directly applying the median filter, change `filter()` so that:

- It starts four workers with the `go` keyword (using a for loop).
- It collects the resulting parts into a single 2D slice (using a for loop and `append`).

Run the filter and make sure the image is correct. It should look like this:

![Parallel median filter result](content/parallelShip.png)

<details>
    <summary>Hint 1</summary>

The workers each need a channel to send their output on. You need to create a slice of 4 channels - one for each worker.

You need to make a slice of type `[]chan [][]uint8` and then, in a for loop, make individual channels of type `chan [][]uint8`.

</details>

<details>
    <summary>Hint 2</summary>

Start 4 workers using the `go` command. For an image of size 512x512 (such as `ship.png`) they need to work on following y-coordinates:

- Worker 1: 0-128
- Worker 2: 128-256
- Worker 3: 256-384
- Worker 3: 384-512

x-coordinates would be 0-512 for all workers

(The ranges here are same as for the slices - e.g for range 128-256, 128 is included but 256 isn't.)

</details>

<details>
    <summary>Hint 3</summary>

To reconstruct the image in a single 2D slice you can collect all the parts from the workers and use `append` to attach the matrices together. E.g.:

```go
newData = append(newData, part...)
```

Where both `newData` and `part` are 2D slices.

</details>

### Question 1d

When parallelising, our main aim is to make the processing faster. Using benchmarks you can measure just how fast your program is. To run a benchmark use the command `go test -bench . -benchtime 10x`. It will run our filter 10 times and return the average time the filter took. Run the benchmark on your new parallel filter as well as the original single-threaded one that you were given.

Compare the results and conclude whether the parallel filter is faster.

### Question 1e

Use the code from `main()` in `ping.go` to generate a trace of your parallel filter. Verify that the filter is processing the image via the worker goroutines.

## **EXTRA** Do these after question 2

### **OPTIONAL** Question 1f

If your processed image has black lines like the one we have shown above it is because you divided the image exactly in 4 parts. For each given pixel of the image, the filter needs neighbours in radius 2 - i.e. given bounds 0-128 it will only process pixels in bounds 2-126.

Fix your code so that the resulting image looks the same as it used to with the single-threaded filter.

### **OPTIONAL** Question 1g

Go traces are quite powerful. You can define tasks and regions in your code and log messages.

Read [this article](https://medium.com/@felipedutratine/user-defined-runtime-trace-3280db7fe209) and experiment with logging messages, and defining tasks and regions in your ping-pong program. The trace generated from the example program from the article looks like this:

(note the Say Hello task, and sayHello/sayGoodbye regions in the 2 goroutines)

![Annotated trace](content/trace4.png)

Try to achieve something similar in `ping.go`.



## Question 2 - Parallel tree reduction :red_circle::red_circle::red_circle::white_circle::white_circle:

So far we explored concurrency with only a handful of goroutines. In this question, you will try using a very large number of goroutines and you will analyse any costs and benefits of doing so. For example, the trace below illustrates over 8000 goroutines working on sorting a slice of size 10,000,000:

![Merge sort trace](content/mergeTrace.png)

### Question 2a

Open `merge.go`. It's a working merge sort program. Your task will be to parallelise the merge sort in the `parallelMergeSort()` function.

Write a parallel merge sort that creates 2 new goroutines at each split point. Run the `main()` function and verify that the printed slice is correctly sorted. After that, run the benchmarks and draw conclusions about the speed of your implementation. You can plot a graph of your benchmarks using the commands:

```bash
$ go get github.com/ChrisGora/benchgraph
$ go test -bench . | benchgraph

```

*Note 1:* If you wish to modify the signature of the `parallelMergeSort()` function, make sure you also modify the calls to that function that happen in `merge_test.go`.

*Note 2:* Doing parallel merge sort on a slice will involve concurrent writes. Normally, this is not recommended. However, in this particular problem, each goroutine will have own section of the slice to work on. Hence passing the slice is correct but still very bug-prone. You have to make sure that there is no overlap between the sections that the goroutines are working on. We provided you with the `merge()` function which was carefully written to avoid bugs and race conditions.

<details>
    <summary>Hint 1</summary>

Start by copying the sequential merge sort into `parallelMergeSort()`.

</details>

<details>
    <summary>Hint 2</summary>

You have to wait for both workers to finish before calling `merge(...)`. This can be done using channels of type `chan bool` or with [WaitGroups](https://gobyexample.com/waitgroups).

</details>

### Question 2b

The parallel version is slower than the sequential one! If you used benchgraph you would've obtained a graph like this:

![Parallel vs Sequential](content/graph2.png)

While goroutines are quite lightweight, this experiment shows that they still have an associated overhead. We can make the parallel merge sort faster by reducing the number of goroutines created.

Firstly, at every split, only one new goroutine is needed rather than two. This concept is illustrated below. It's a parallel tree reduction where the operation is addition (rather than a merge sort) on 8 elements.

*Note:* Although the animation shows 8 threads for clarity all odd threads are redundant as they only pass a message to a thread to their left and don't perform any computation.

![Parallel tree reduction](https://upload.wikimedia.org/wikipedia/commons/e/ee/Binomial_tree.gif)

Run benchmarks and analyse the performance of your new algorithm. Given a slice of size `n` state how many goroutines your first version would've used and how many your new version now uses.

<details>
    <summary>Hint</summary>

When splitting right start a new goroutine. When splitting left, do a simple recursive function call. Make sure you do the splitting in that order (new goroutine first and function call second).

</details>

### Question 2c

Modify your `parallelMergeSort()` so that below a certain length of the slice it stops spawning new goroutines and instead calls the sequential `mergeSort()`.

Experiment with different thresholds and try to empirically find an optimal one that provides the biggest speed-up.

<details>
    <summary>Our analysis...</summary>

In our experiments on an 8 core machine we have found that `1 << 13` ( = 8192) performs (almost)best. This is not a magic number and there may be a reason behind its speed: The Intel Core i5 processor that we ran the merge sort on has one block of 32KiB L1 cache for each core. This means we can fit in 8192 32-bit integers in that space. The actual fastest constant was 4096 and we have no apparent reason for the fact that it is marginally faster. Note that the lab machines have an i7 processor with 6 cores so your results may vary.

[Java's parallel sort was designed in a very similar way.](http://blog.teamleadnet.com/2014/05/java-8-parallel-sort-internals.html)

 Make sure you also experiment with other values. Thresholds lower than the optimum will cause a bottleneck due to goroutine creation and communication. Thresholds greater than the optimum will cause more cache misses and eventually reduce the level of parallelism. If the threshold is greater than the size of the initial slice the algorithm will stop being parallel.

To investigate different approaches we have written some benchmarks on large slices:

```go

const (
	start = 1048576
	end   = 4194304
)

func BenchmarkSequential(b *testing.B) {
	for size := start; size <= end; size *= 2 {
		b.Run(fmt.Sprint(size), func(b *testing.B) {
			os.Stdout = nil // Disable all program output apart from benchmark results
			for i := 0; i < b.N; i++ {
				unsorted := random(size)
				b.StartTimer()
				mergeSort(unsorted)
				b.StopTimer()
			}
		})
	}
}

func Benchmark512(b *testing.B) {
	for size := start; size <= end; size *= 2 {
		b.Run(fmt.Sprint(size), func(b *testing.B) {
			os.Stdout = nil // Disable all program output apart from benchmark results
			for i := 0; i < b.N; i++ {
				unsorted := random(size)
				b.StartTimer()
				parallelMergeSort(unsorted, 512)
				b.StopTimer()
			}
		})
	}
}

func Benchmark1024(b *testing.B) {
	for size := start; size <= end; size *= 2 {
		b.Run(fmt.Sprint(size), func(b *testing.B) {
			os.Stdout = nil // Disable all program output apart from benchmark results
			for i := 0; i < b.N; i++ {
				unsorted := random(size)
				b.StartTimer()
				parallelMergeSort(unsorted, 1024)
				b.StopTimer()
			}
		})
	}
}

func Benchmark2048(b *testing.B) {
	for size := start; size <= end; size *= 2 {
		b.Run(fmt.Sprint(size), func(b *testing.B) {
			os.Stdout = nil // Disable all program output apart from benchmark results
			for i := 0; i < b.N; i++ {
				unsorted := random(size)
				b.StartTimer()
				parallelMergeSort(unsorted, 2048)
				b.StopTimer()
			}
		})
	}
}

func Benchmark4096(b *testing.B) {
	for size := start; size <= end; size *= 2 {
		b.Run(fmt.Sprint(size), func(b *testing.B) {
			os.Stdout = nil // Disable all program output apart from benchmark results
			for i := 0; i < b.N; i++ {
				unsorted := random(size)
				b.StartTimer()
				parallelMergeSort(unsorted, 4096)
				b.StopTimer()
			}
		})
	}
}
//
func Benchmark8192(b *testing.B) {
	for size := start; size <= end; size *= 2 {
		b.Run(fmt.Sprint(size), func(b *testing.B) {
			os.Stdout = nil // Disable all program output apart from benchmark results
			for i := 0; i < b.N; i++ {
				unsorted := random(size)
				b.StartTimer()
				parallelMergeSort(unsorted, 8192)
				b.StopTimer()
			}
		})
	}
}
//
func Benchmark32768(b *testing.B) {
	for size := start; size <= end; size *= 2 {
		b.Run(fmt.Sprint(size), func(b *testing.B) {
			os.Stdout = nil // Disable all program output apart from benchmark results
			for i := 0; i < b.N; i++ {
				unsorted := random(size)
				b.StartTimer()
				parallelMergeSort(unsorted, 32768)
				b.StopTimer()
			}
		})
	}
}

func Benchmark16384(b *testing.B) {
	for size := start; size <= end; size *= 2 {
		b.Run(fmt.Sprint(size), func(b *testing.B) {
			os.Stdout = nil // Disable all program output apart from benchmark results
			for i := 0; i < b.N; i++ {
				unsorted := random(size)
				b.StartTimer()
				parallelMergeSort(unsorted, 16384)
				b.StopTimer()
			}
		})
	}
}

func BenchmarkDivGOMAX(b *testing.B) {
	for size := start; size <= end; size *= 2 {
		b.Run(fmt.Sprint(size), func(b *testing.B) {
			os.Stdout = nil // Disable all program output apart from benchmark results
			for i := 0; i < b.N; i++ {
				unsorted := random(size)
				b.StartTimer()
				parallelMergeSort(unsorted, size/runtime.NumCPU())
				b.StopTimer()
			}
		})
	}
}

```

We have then ran the benchmarks and analysed the results with the benchgraph library:

```bash
$ go test -bench . | benchgraph

```

![Graph](content/graph1.png)

</details>
