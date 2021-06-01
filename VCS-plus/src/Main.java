import static java.lang.Math.*;
import static java.util.Arrays.*;

import java.io.*;
import java.util.*;

import tc.wata.debug.*;
import tc.wata.io.*;
import tc.wata.util.*;
import tc.wata.util.SetOpt.*;

public class Main {
    public static final String VERSION = "1.2";
    public static final String MODIFICATION_DATE = "February 2020";
    
    @Option(abbr = 'b', usage = "0: random, 1: mindeg, 2: maxdeg")
    public static int branching = 2;

    @Option(abbr = 'o')
    public static boolean outputLP = false;

    @Option(abbr = 'd', usage = "0: no debug output, 1: basic branching and decompose, 2: detailed branching and decompose and basic reduction, 3: detailed reduction")
    public static int debug = 0;

    @Option(abbr = 't', usage = "timeout in seconds")
    public static int timeout = 3600;

    @Option(name = "trace", usage = "0: no trace, 1: short version without solution vectors, 2: full trace with solution vectors")
    public static int trace = 0;

    @Option(name = "quiet", usage = "Don't print progress messages (useful if running with detached screen)")
    public static boolean quiet = false;

    @Option(name = "root", usage = "Only process root node -- no branching")
    public static boolean only_root = false;

    @Option(name = "show_solution", usage = "Enable printing of solution vector")
    public static boolean show_solution = false;

    // Lower bound options
    @Option(name = "clique_lb", usage = "Enable clique lower bound")
    public static boolean clique_lb = false;

    @Option(name = "lp_lb", usage = "Enable lp lower bound")
    public static boolean lp_lb = false;

    @Option(name = "cycle_lb", usage = "Enable cycle lower bound")
    public static boolean cycle_lb = false;

    // Reduction options
    @Option(name = "deg1", usage = "Enable degree1 reduction")
    public static boolean degree1_reduction = false;

    @Option(name = "dom", usage = "Enable dominance reduction")
    public static boolean dominance_reduction = false;

    @Option(name = "fold2", usage = "Enable fold2 reduction")
    public static boolean fold2_reduction = false;

    @Option(name = "LP", usage = "Enable LP reduction")
    public static boolean lp_reduction = false;

    @Option(name = "unconfined", usage = "Enable unconfined reduction")
    public static boolean unconfined_reduction = false;

    @Option(name = "twin", usage = "Enable twin reduction")
    public static boolean twin_reduction = false;

    @Option(name = "funnel", usage = "Enable funnel reduction")
    public static boolean funnel_reduction = false;

    @Option(name = "desk", usage = "Enable desk reduction")
    public static boolean desk_reduction = false;

    @Option(name = "packing", usage = "Enable packing reduction")
    public static boolean packing_reduction = false;

    // All flag
    @Option(name = "all_red", usage = "Enable all reductions except packing, equivalent to old '-r2 -l3'")
    public static boolean all_reductions = false;

    // Preprocess
    // @Option(name = "preprocess", usage = "Flag that enables preprocessing to determine which reductions are enabled. Any user selected reductions are ignored. Currently, only the deg1, dom, and LP reductions are considered.")
    public static boolean preprocess_reductions = false;

    // Selective reductions based on measures
    // @Option(name = "selective", usage = "If the deg1, dom, or LP reductions are enabled, then only apply them if some threshold is met.")
    public static boolean selective = false;

    // Thresholds
    // @Option(name = "oc", usage = "Sets the oc threshold to enable lp reduction, i.e., if the oc is < value then use lp")
    public static double oc_threshold = 1.00;

    // @Option(name = "dv", usage = "Sets the dv threshold to enable deg1 and dominance reductions, i.e., if the dv is > value then use deg1 and dominance")
    public static double dv_threshold = 0.00;

    // @Option(name = "min_density", usage = "Sets the minumum density threshold to enable deg1 and dominance reductions, i.e., if the density is > value then use deg1 and dominance")
    public static double min_density_threshold = 0.00;

    // @Option(name = "max_density", usage = "Sets the maximum density threshold to enable deg1 and dominance reductions, i.e., if the density is < value then use deg1 and dominance")
    public static double max_density_threshold = 1.00;

    // General selective reduction options
    // @Option(name = "disable", usage = "Disable reductions if efficiency is below some threshold")
    public static boolean disable = false;

    // @Option(name = "tiered_disable", usage = "Disable reductions if efficiency is below some threshold")
    public static boolean tiered_disable = false;

    // @Option(name = "density_skip", usage = "Skip all reductions except degree1, dominance, and packing if the density is greater than 0.5")
    public static boolean density_skip = false;

    // @Option(name = "size", usage = "Graph size threshold to enable reductions (1.00 means use reductions from the start")
    public static double size_skip = 1.00;

    /**
     * so that runtime-relevant information can be accessed from routine that prints it
     */
    long start;
    long end;
    long totalRuntime;
    String runStatus = "Normal";
    
    void printVersionInfo() {
        System.out.println("Akiba-Iwata branch and reduce solver,"
                           + " modified by Yang Ho and Matthias Stallmann");
        System.out.println(" version " + VERSION  + ", " + MODIFICATION_DATE);
    }

  /**
   * conversion from internal index to original vertex id; so vertexID[i] is
   * the original (external) id of the vertex whose index is i.
   */
    int[] vertexID;
    int[][] adj;
    double mean_degree;

    // Compute oc value 
    boolean[] marked, color;
    int oc_count;
    int num_edges;

    void ocDFS(int u) {
        marked[u] = true;
        for (int v : adj[u]) {
            num_edges += 1;
            if (!marked[v]) {
                color[v] = !color[u];
                ocDFS(v);
            } else if (color[v] == color[u]) {
                oc_count += 1;
            }
        }
    }

    long oc_start_time;
    long oc_end_time;
    double getOC() {
        oc_start_time = System.nanoTime();
        oc_count = 0;
        num_edges = 0;
        int n = adj.length;
        marked = new boolean[n];
        color = new boolean[n];
        for (int i = 0; i < n; i++) {
            marked[i] = false;
            color[i] = false;
        }

        for (int i = 0; i < n; i++) {
            if (!marked[i]) {
                color[i] = true;
                ocDFS(i);
            }
        }
        oc_end_time = System.nanoTime();
        System.out.println(oc_count);
        return (double) 2 * oc_count / num_edges;
    }

    void read(String file) {
        if (file.endsWith(".dat")) {
            GraphIO io = new GraphIO();
            io.read(new File(file));
            adj = io.adj;
            vertexID = new int[adj.length];
            for (int i = 0; i < adj.length; i++) vertexID[i] = i;
            mean_degree = io.mean_degree;
        } else {
            GraphConverter conv = new GraphConverter();
            conv.file = file;
            conv.type = "snap";
            conv.undirected = true;
            conv.sorting = true;
            try {
                conv.read();
            } catch (Exception e) {
                conv = new GraphConverter();
                conv.file = file;
                conv.type = "dimacs";
                conv.undirected = true;
                conv.sorting = true;
                try {
                    conv.read();
                } catch (IOException ex) {
                    throw new RuntimeException(ex);
                }
            }
            adj = conv.adj;
            vertexID = conv.vertexID;
            mean_degree = conv.mean_degree;
        }
        // give VCSolver the ability to convert from index to original vertex id
        VCSolver.vertexID = vertexID;
    }

    /**
     * report all statistics
     */
    void report(VCSolver vc) {
        System.out.format(VCSolver.STRING_REPORT_FORMAT,
                          "status", runStatus);
        System.out.format(VCSolver.COUNT_REPORT_FORMAT,
                          "value", vc.optimal_value);
        end = System.nanoTime();
        totalRuntime = end - start;
        System.out.format(VCSolver.RUNTIME_REPORT_FORMAT,
                          "runtime", 1e-9 * totalRuntime);
        System.out.format(VCSolver.COUNT_REPORT_FORMAT,
                          "num_branches", VCSolver.nBranchings);

        // special information, relevant only to experiments where we
        // conditionally applied degree-one/dominance reductions (large
        // degree variance) or lp reductions (small oct)
        if ( preprocess_reductions ) {
            System.out.format(VCSolver.RUNTIME_REPORT_FORMAT, "base_ocTime(ms)",
                              1e-6 * (oc_end_time - oc_start_time));
        }
        if ( VCSolver.total_oc_time > 0 ) {
                System.out.format(VCSolver.RUNTIME_REPORT_FORMAT, "ocTime(ms)",
                                  1e-6 * VCSolver.total_oc_time);
        }
        if ( VCSolver.total_dv_time > 0 ) {
            System.out.format(VCSolver.RUNTIME_REPORT_FORMAT, "dvTime(ms)",
                              1e-6 * VCSolver.total_dv_time);
        }

        /**
         * @todo make all reporting consistent, i.e., call on methods of
         * VCSolver to do the job, as with LB counts and times.
         * Furthermore, reporting should go into a separate method, that
         * can be called even if the solver crashes
         */
        System.out.format("%s:\n", "Reduction Times (ms)");
        System.out.format(VCSolver.RUNTIME_REPORT_FORMAT,
                          "deg1Time", 1e-6 * VCSolver.degTime);
        System.out.format(VCSolver.RUNTIME_REPORT_FORMAT,
                          "domTime", 1e-6 * VCSolver.domTime);
        System.out.format(VCSolver.RUNTIME_REPORT_FORMAT,
                          "fold2Time", 1e-6 * VCSolver.foldTime);
        System.out.format(VCSolver.RUNTIME_REPORT_FORMAT,
                          "lpTime", 1e-6 * VCSolver.lpTime);
        System.out.format(VCSolver.RUNTIME_REPORT_FORMAT,
                          "twinTime", 1e-6 * VCSolver.twinTime);
        System.out.format(VCSolver.RUNTIME_REPORT_FORMAT,
                          "deskTime", 1e-6 * VCSolver.deskTime);
        System.out.format(VCSolver.RUNTIME_REPORT_FORMAT,
                          "unconfinedTime", 1e-6 * VCSolver.unconfinedTime);
        System.out.format(VCSolver.RUNTIME_REPORT_FORMAT,
                          "funnelTime", 1e-6 * VCSolver.funnelTime);
        System.out.format(VCSolver.RUNTIME_REPORT_FORMAT,
                          "packingTime", 1e-6 * VCSolver.packingTime);
        System.out.format("%s:\n", "Vertices Reduced");
        if ( vc != null ) {
            vc.printReduceAmounts();
            System.out.format("%s:\n", "Effective Reduction Calls");
            vc.printEffectiveReduceCalls();
            System.out.format("%s:\n", "Total Reduction Calls");
            vc.printReduceCalls();
        }
        VCSolver.printLBCounts();
        VCSolver.printLBRuntimes();
    }
    
    void run(String file, String[] arguments_before_processing) {
        System.err.println("reading the input graph...");
        read(file);
        if (debug > 0) Stat.setShutdownHook();

        // preprocces 
        int m = 0;
        double sum_square = 0;
        for (int i = 0; i < adj.length; i++) {
            int deg_i = adj[i].length;
            m += deg_i;
            double diff = deg_i - mean_degree;
            sum_square += (diff * diff);
        }
        double root_dv = sqrt(sum_square / (adj.length - 1)) / mean_degree;
        m /= 2;

        System.out.format("%s %s\n", "InputFile   \t", file);
        System.out.format("%s"     , "Options     \t");
        for ( int i = 0; i < arguments_before_processing.length - 1; i++ ) {
            // apparently, the part of an option string starting at '_', or
            // probably any other special character, is ignored
            if ( arguments_before_processing[i].equals("--all_red")
                 || arguments_before_processing[i].equals("--all") ) {
                System.out.format(":--deg1:--dom:--fold2:--LP:--unconfined:--twin:--funnel:--desk:--clique_lb:--lp_lb");
            } else {
                System.out.format(":%s", arguments_before_processing[i]);
            }
        }
        System.out.println();
        System.out.format(VCSolver.COUNT_REPORT_FORMAT, "num_vertices", adj.length);
        System.out.format(VCSolver.COUNT_REPORT_FORMAT, "num_edges", m);

        // deprecated: this information is easy to calculate externally and
        // may not be relevant
        // System.out.format("%s %f\n", "Root_mean_deg\t", mean_degree);
        // System.out.format("%s %f\n", "Root_dv     \t", root_dv);

        VCSolver vc = new VCSolver(adj, adj.length);
        VCSolver.nBranchings = 0;
        VCSolver.nLeftCuts = 0;

        /**
         * @todo The logic below is awkward.  If all_reductions is true, the
         * appropriate variables for class Main should be set above.
         */
        if (all_reductions) {
            clique_lb = true;
            lp_lb = true;
            // if (preprocess_reductions) {
            //     if (root_dv > dv_threshold) {
            //         degree1_reduction = true;
            //         dominance_reduction = true;
            //     } else {
            //         double root_oc = getOC();
            //         if (root_oc < oc_threshold) {
            //             lp_reduction = true;
            //         }
            //         System.out.format("%s %f\n", "Root_oc \t", root_oc);
            //     }
            // }
            // else {
                degree1_reduction = true;
                dominance_reduction = true;
                fold2_reduction = true;
                lp_reduction = true;
                unconfined_reduction = true;
                twin_reduction = true;
                funnel_reduction = true;
                desk_reduction = true;
                //packing_reduction = true;
            // }
        }
        // else if (preprocess_reductions) {
        //     degree1_reduction = false;
        //     dominance_reduction = false;
        //     fold2_reduction = false;
        //     lp_reduction = false;
        //     unconfined_reduction = false;
        //     twin_reduction = false;
        //     funnel_reduction = false;
        //     desk_reduction = false;
        //     packing_reduction = false;
            // if (root_dv > dv_threshold) {
            //     degree1_reduction = true;
            //     dominance_reduction = true;
            // } else {
            //     double root_oc = getOC();
            //     if (root_oc < oc_threshold) {
            //         lp_reduction = true;
            //     }
            //     System.out.format("%s %f\n", "Root_oc \t", root_oc);
            // }
        // }

        VCSolver.DEGREE1_REDUCTION = degree1_reduction;
        VCSolver.DOMINANCE_REDUCTION = dominance_reduction;
        VCSolver.FOLD2_REDUCTION = fold2_reduction;
        VCSolver.LP_REDUCTION = lp_reduction;
        VCSolver.UNCONFINED_REDUCTION = unconfined_reduction;
        VCSolver.TWIN_REDUCTION = twin_reduction;
        VCSolver.FUNNEL_REDUCTION = funnel_reduction;
        VCSolver.DESK_REDUCTION = desk_reduction;
        VCSolver.PACKING_REDUCTION = packing_reduction;

        VCSolver.CLIQUE_LOWER_BOUND = clique_lb;
        VCSolver.LP_LOWER_BOUND = lp_lb;
        VCSolver.CYCLE_LOWER_BOUND = cycle_lb;

        VCSolver.TRACE = trace;
        VCSolver.QUIET = quiet;

        VCSolver.BRANCHING = branching;
        VCSolver.outputLP = outputLP;
        VCSolver.DEBUG = debug;
        VCSolver.ONLY_ROOT = only_root;

        VCSolver.DISABLE_REDUCTIONS = disable;
        VCSolver.TIERED_DISABLE = tiered_disable;

        VCSolver.DENSITY_REDUCTIONS = density_skip;
        VCSolver.REDUCTION_SIZE_THRESHOLD = size_skip;

        if (selective) {
            VCSolver.OC_LP_THRESHOLD = oc_threshold;
            VCSolver.DV_DD_THRESHOLD = dv_threshold;
            VCSolver.MIN_DENSITY_THRESHOLD = min_density_threshold;
            VCSolver.MAX_DENSITY_THRESHOLD = max_density_threshold;
        }

        if (debug >= 2) {
            System.err.println("Graph:");
            for (int i = 0; i < adj.length; i++) {
                System.err.format("%d: ", i);
                for (int j = 0; j < adj[i].length; j++) {
                    System.err.format("%d ", adj[i][j]);
                }
                System.err.println();
            }
            System.err.println("=====");
        }
        try (Stat stat = new Stat("solve")) {
            start = System.nanoTime();
            VCSolver.startTime = 1e-9 * start;
            VCSolver.timelimit = 1e-9 * start + timeout;
            vc.solve();
            report(vc);

            // read file again so that solution can be printed
            read(file);
            int sum = 0;
            for (int i = 0; i < adj.length; i++) {
                sum += vc.optimal_solution[i];
                Debug.check(vc.optimal_solution[i] == 0 || vc.optimal_solution[i] == 1);
                for (int j : adj[i]) Debug.check(vc.optimal_solution[i] + vc.optimal_solution[j] >= 1);
            }
            Debug.check(sum == vc.optimal_value);
            if (debug > 0) {
                System.out.printf("%d\t%d\t%d\t%.3f\t%d%n", adj.length, m, vc.optimal_value, 1e-9 * (end - start), VCSolver.nBranchings);
            }
            System.out.format(VCSolver.COUNT_REPORT_FORMAT,
                              "num_leftcuts", VCSolver.nLeftCuts);
            System.out.format(VCSolver.COUNT_REPORT_FORMAT,
                              "root_lb", VCSolver.lbAtRoot);
            if (show_solution) {
                System.out.format("%s %s\n", "solution\t", VCSolver.solutionToString(vc.optimal_solution));
            }
        } catch (OutOfMemoryError e) {
            /**
             * @todo catch all runtime errors (and make a timeout an error);
             * then report statistics regardless of error, but include a
             * ProvedOptimal output line to be consistent with CPLEX
             */
            runStatus = "MemoryLimit";
            System.err.println(e);
            report(vc);
            System.exit(1);
        } catch (AbortTimeLimit e) {
            runStatus = "Timeout";
            System.err.println(e);
            report(vc);
            System.exit(1);
        } catch (Throwable e) {
            runStatus = "Exception";
            System.err.println(e);
            report(vc);
            e.printStackTrace(System.err);
            System.exit(1);
        }
    }

    void debug(Object...os) {
        System.err.println(deepToString(os));
    }

    public static void main(String[] args) {
        Main main = new Main();
        main.printVersionInfo();
        String[] arguments_before_processing = args;
        args = SetOpt.setOpt(main, args);
        if (args.length > 0) {
            main.run(args[0], arguments_before_processing);
        } else {
            System.err.printf("Missing required argument: file_name; for help, use --help%n");
        }
    }
}

//  [Last modified: 2020 02 06 at 22:51:06 GMT]
