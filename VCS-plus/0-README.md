## Instructions for running `VCS-plus`

* To compile:
`./build.sh`

* To see list of available options do
`java -cp bin Main --help`

* To run
`java -cp bin Main [OPTIONS] INPUT_FILE`
__Note:__ _Running with no options causes all reductions and all lower bounds to be disabled._ To run with a standard set of options, like those recommended in _Branch-and-reduce exponential/FPT algorithms in practice: A case study of vertex cover_ (T, Akiba and Y. Iwata):
`java -cp bin Main --all [INPUT_FILE]`
This will enable all reductions except for packing and all lower bounds except for the cycle cover lower bound.

* You can use [snap](http://snap.stanford.edu/data/) or [dimacs](http://archive.dimacs.rutgers.edu/Challenges/) format.

Sources of input graphs:
- [http://snap.stanford.edu/data/](http://snap.stanford.edu/data/)
- http://konect.uni-koblenz.de/
- http://law.di.unimi.it/datasets.php
- http://www.cs.hbg.psu.edu/txn131/vertex_cover.html
- http://www.user.tu-berlin.de/hueffner/occ/
