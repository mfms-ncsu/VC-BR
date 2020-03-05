/**
 * Can be used for timeouts in programs, so that the sequence of events when
 * a timeout occurs is more transparent. 
 */

public class AbortTimeLimit extends Throwable {
    AbortTimeLimit(double limit, double elapsedTime) {
        super(String.format("Time limit %10.2f exceeded, elapsed time is %10.2f",
                            limit, elapsedTime));
    }
}

//  [Last modified: 2020 02 06 at 22:31:43 GMT]
