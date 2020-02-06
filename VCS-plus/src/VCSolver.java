import static java.util.Arrays.*;

import java.util.*;
import java.io.*;

import tc.wata.data.*;
import tc.wata.debug.*;

public class VCSolver {

    /** number of seconds between "progress reports" */
    private static final double PRINT_INTERVAL = 60.0;
    /** time of previous progress report */
    private static double previous = 0.0;

    public static int lbAtRoot = 0;

    /**
     * type of most recent lower bound calculated; used to keep track of
     * success of various types of lower bounds
     */
    public enum LowerBoundType {
        TRIVIAL,                // use current value
        CLIQUE,                 // clique cover
        LP,                     // linear programming with extreme solution
        CYCLE                   // cycle cover
    }

    LowerBoundType lbType;
    
    // strings for each lower bound type, to be printed in a trace
    static final String TRIVIAL_LB_STRING = "trv_lb";
    static final String CLIQUE_LB_STRING = "clq_lb";
    static final String LP_LB_STRING = "lp_lb";
    static final String CYCLE_LB_STRING = "cyc_lb";

    /**
     * @return a string representation of the lower bound type, to be used
     * for tracing
     */
    static String getLBTypeString(LowerBoundType type) {
        if ( type == LowerBoundType.TRIVIAL ) return TRIVIAL_LB_STRING;
        if ( type == LowerBoundType.CLIQUE ) return CLIQUE_LB_STRING;
        if ( type == LowerBoundType.LP ) return LP_LB_STRING;
        if ( type == LowerBoundType.CYCLE ) return CYCLE_LB_STRING;
        // the following is a placeholder to make the compiler happy
        return "*** unrecognized LB type ***";
    }

    // number of times each lower bound is effective
    static long trivialLBCount = 0;
    static long cliqueLBCount = 0;
    static long lpLBCount = 0;
    static long cycleLBCount = 0;

    /**
     * increments the number of times a lower bound of the given type is effective
     */
    static void incrementLBCount(LowerBoundType type) {
        if ( type == LowerBoundType.TRIVIAL ) trivialLBCount++;
        if ( type == LowerBoundType.CLIQUE ) cliqueLBCount++;
        if ( type == LowerBoundType.LP ) lpLBCount++;
        if ( type == LowerBoundType.CYCLE ) cycleLBCount++;
    }

    /**
     * format for printing all types of counts, preceded by their tags
     */
    public static final String COUNT_REPORT_FORMAT = "%-20s\t%16d\n";
    
    /**
     * format for printing all runtimes, preceded by their tags
     */
    public static final String RUNTIME_REPORT_FORMAT = "%-20s\t%10.2f\n";
    
    /**
     * prints the number of times each lower bound type was effective, in a
     * format consistent with other reports
     */
    public static void printLBCounts() {
        System.out.printf("%s:\n", "Effective Lower Bounds");
        System.out.printf(COUNT_REPORT_FORMAT, "trivialLBCount", trivialLBCount); 
        System.out.printf(COUNT_REPORT_FORMAT, "cliqueLBCount", cliqueLBCount); 
        System.out.printf(COUNT_REPORT_FORMAT, "lpLBCount", lpLBCount); 
        System.out.printf(COUNT_REPORT_FORMAT, "cycleLBCount", cycleLBCount); 
    }

    /**
     * prints the amount of time taken for each lower bound type in a format
     * consistent with other reports
     * note: only relevant for clique and cycle lower bounds; the others
     * don't take additional time
     */
    public static void printLBRuntimes() {
        System.out.printf("%s:\n", "Lower Bound Times (ms)");
        System.out.printf(RUNTIME_REPORT_FORMAT, "cliqueLBTime", 1e-6 * cliqueTime); 
        System.out.printf(RUNTIME_REPORT_FORMAT, "cycleLBTime", 1e-6 * cycleTime); 
    }
    
    // Node status strings printed in trace
    public static final String NODE_RED_CUT_STRING = "red_cut";
    public static final String NODE_LB_CUT_STRING = "/ lb_cut";
    public static final String NODE_SOLVED_STRING = "= solved";
    public static final String NODE_ALIVE_STRING = "- alive";

    // Reduction string for when vertices are reduced
    public static String red_source = "";
    public static final String VERTEX_DEG1_STRING = "deg1_red"; 
    public static final String VERTEX_DOM_STRING = "dom_red"; 
    public static final String VERTEX_UNCONFINED_STRING = "uncon_red"; 
    public static final String VERTEX_FOLD2_STRING = "fold2_red";
    public static final String VERTEX_TWIN_STRING = "twin_red";
    public static final String VERTEX_FUNNEL_STRING = "funnel_red";
    public static final String VERTEX_DESK_STRING = "desk_red";
    public static final String VERTEX_LP_STRING = "lp_red";

    public static int CLIQUE_STAT_MAX_CLIQUE_SIZE = 0;
    public static int CLIQUE_STAT_CLIQUE_COUNT = 0;

    public static Random rand = new Random(4327897);

    // Which lower bound to use
    public static boolean CLIQUE_LOWER_BOUND = true;
    public static boolean LP_LOWER_BOUND = true;
    public static boolean CYCLE_LOWER_BOUND = true;

    public static int BRANCHING = 2;

    // Disable reductions after root
    public static boolean DISABLE_REDUCTIONS = false;
    public static boolean TIERED_DISABLE = false;
    double DISABLE_EFFICIENCY_THRESHOLD = 0.5;

    // Skip reductions based on density
    public static boolean DENSITY_REDUCTIONS = false;
    double DENSITY_SKIP_THRESHOLD = 0.5;

    // Skip reductions based on size
    public static double REDUCTION_SIZE_THRESHOLD = 1.00;
    int TARGET_SIZE;

    // Reduction thresholds:
    public static double DV_DD_THRESHOLD = 0.00;
    public static double OC_LP_THRESHOLD = 1.00;
    public static double MIN_DENSITY_THRESHOLD = 0.00;
    public static double MAX_DENSITY_THRESHOLD = 1.00;
    public static long total_oc_time = 0;
    public static long total_dv_time = 0;

    // Which reductions to use
    public static boolean DEGREE1_REDUCTION = true;
    public static boolean DOMINANCE_REDUCTION = true;
    public static boolean FOLD2_REDUCTION = true;
    public static boolean LP_REDUCTION = true;
    public static boolean UNCONFINED_REDUCTION = true;
    public static boolean TWIN_REDUCTION = true;
    public static boolean FUNNEL_REDUCTION = true;
    public static boolean DESK_REDUCTION = true;
    public static boolean PACKING_REDUCTION = true;

    // Only process the root node
    public static boolean ONLY_ROOT = false;

    // Debug related options
    public static int TRACE = 0;
    public static boolean QUIET = false;

    public static int DEBUG = 3;

    public static boolean outputLP = true;

    public boolean INITIAL_REDUCTION;

    // Additional output statistics
    public static long nBranchings;
    public static int nLeftCuts;
    public static double startTime = 0;
    public static double timelimit = 0;
    // time taken for various reduction types
    public static long lpTime = 0;
    public static long domTime = 0;
    public static long degTime = 0;
    public static long foldTime = 0;
    public static long twinTime = 0;
    public static long funnelTime = 0;
    public static long deskTime = 0;
    public static long unconfinedTime = 0;
    public static long packingTime = 0;
    
    // time taken for lower bounds
    // note: trivial and lp don't require additional time
    public static long cliqueTime = 0;
    public static long cycleTime = 0;
    
    boolean component = false;

    int depth = 0, maxDepth = 10, rootDepth;

    double SHRINK = 0.5;

    // Information about the graph
    public int n, N;
    public int[][] adj;
    double density = 1.0; // The actual density of the graph not edge density

    /**
     * This can be static because there's apparently only one instance of
     * VCSolver.
     * It is described in Main.java, where, for now, it is created.
     * @todo there is more than one instance if we break into components, so we
     * need to rethink
     */
    static int [] vertexID;

    /**
     * current best solution
     */
    public int optimal_value, optimal_solution[];

    /**
     * current solution 
     *   -1: not determined,
     *    0: not in the vc,
     *    1: in the vc,
     *    2: removed by foldings
     */
    int current_value, curr_solution[];

    /**
     * number of remaining vertices
     */
    int remaining_vertices;

    /**
     * a stack of vertices whose values have been set in the current
     * (sub)instance and should therefore be restored to their undecided
     * state when the current recursive call is done
     */
    int restore[];

    /**
     * max flow
     * in_flow = flow from L vertices
     * out_flow = flow to R vertices
     */
    int[] in_flow, out_flow;

    /**
     * lower bound
     */
    int lb;

    /**
     * Packing constraints
     */
    ArrayList<int[]> packing;

    static enum REDUCE_TYPES {
        DEG_ONE,
        DOMINANCE,
        FOLD_TWO,
        LP,
        TWIN,
        DESK,
        UNCONFINED,
        FUNNEL,
        PACKING
    };
    static int[] reduce_counts = new int[REDUCE_TYPES.values().length];
    static int[] reduce_effective_counts = new int[REDUCE_TYPES.values().length];
    String[] reduce_types;

    int[] degTmp;

    public VCSolver(int[][] adj, int N) {
        n = adj.length;
        this.N = N;
        this.adj = adj;
        optimal_value = n;
        optimal_solution = new int[N];
        for (int i = 0; i < n; i++) optimal_solution[i] = 1;
        for (int i = n; i < N; i++) optimal_solution[i] = 2;
        current_value = 0;
        curr_solution = new int[N];
        for (int i = 0; i < n; i++) curr_solution[i] = -1;
        for (int i = n; i < N; i++) curr_solution[i] = 2;
        remaining_vertices = n;
        used = new FastSet(n * 2);
        restore = new int[n];
        modifieds = new Modified[N];
        modifiedN = 0;
        in_flow = new int[n];
        out_flow = new int[n];
        fill(in_flow, -1);
        fill(out_flow, -1);
        que = new int[n * 2];
        level = new int[n * 2];
        iter = new int[n * 2];
        packing = new ArrayList<int[]>();
        modTmp = new int[n];

        // Measure related
        degTmp = new int[n];
        marked = new boolean[n];
        color = new boolean[n];


        INITIAL_REDUCTION = false;
        reduce_types = new String[REDUCE_TYPES.values().length];
        reduce_types[REDUCE_TYPES.DEG_ONE.ordinal()] = "deg1";
        reduce_types[REDUCE_TYPES.DOMINANCE.ordinal()] = "dom";
        reduce_types[REDUCE_TYPES.UNCONFINED.ordinal()] = "unconfined";
        reduce_types[REDUCE_TYPES.LP.ordinal()] = "lp";
        reduce_types[REDUCE_TYPES.PACKING.ordinal()] = "packing";
        reduce_types[REDUCE_TYPES.FOLD_TWO.ordinal()] = "fold2";
        reduce_types[REDUCE_TYPES.TWIN.ordinal()] = "twin";
        reduce_types[REDUCE_TYPES.FUNNEL.ordinal()] = "funnel";
        reduce_types[REDUCE_TYPES.DESK.ordinal()] = "desk";

        TARGET_SIZE = (int) (n * REDUCTION_SIZE_THRESHOLD);
    }

    /**
     * @return a string representation of the internal solution, which is
     * indexed by indexes created by the solver, in terms of original id's of
     * the vertices; the string has, at position v, a
     *    1 if vertex v is in the cover
     *    0 if vertex v is not in the cover
     *    x if solution at v is still undecided
     *    - if v is in a different component
     *    _ if no vertex with that id exists in the graph
     */
    static String solutionToString(int [] internal_solution) {
        int maxVertexId = 0;
        for ( int i = 0; i < vertexID.length; i++ ) {
            if ( vertexID[i] > maxVertexId ) maxVertexId = vertexID[i];
        }
        // positions go from 1 to maxVertexId
        char [] solutionString = new char[maxVertexId + 1];
        for ( int i = 0; i < solutionString.length; i++ ) solutionString[i] = '_';
        for ( int i = 0; i < vertexID.length; i++ ) {
            int index = vertexID[i];
            if (index < 0) {
                index = 0;
            }
            if ( i >= internal_solution.length) {
                solutionString[index] = '-';
            }
            else if ( internal_solution[i] == 1 ) {
                solutionString[index] = '1';
            }
            else if ( internal_solution[i] == 0 ) {
                solutionString[index] = '0';
            }
            else if ( internal_solution[i] == -1 ) {
                solutionString[index] = 'x';
            }
        }
        return new String(solutionString);
    }

    public void isComponentSolve() {
        component = true;
    }

    // public void printReduceTimes() {
    //     for (int i = 0; i < reduce_types.length; i++) {
    //         System.out.format("%s %10.3f\n", "funnelTime     \t", 1e-6 * VCSolver.funnelTime);           System.out.printf("%-20s\t%10d\n", reduce_types[i] + "", Stat.getCount("reduceN_" + reduce_types[i]));
    //     }
    // }
    public void printReduceAmounts() {
        for (int i = 0; i < reduce_types.length; i++) {
            System.out.printf(COUNT_REPORT_FORMAT,
                              reduce_types[i] + "Count",
                              Stat.getCount("reduceN_" + reduce_types[i]));
        }
        // !!! omit for now, unless there's a clearer explanation !!!
        // System.out.printf(COUNT_REPORT_FORMAT,
        //                   "diamondCount", Stat.getCount("reduceN_diamond"));
    }
    public void printReduceCalls() {
        for (int i = 0; i < reduce_types.length; i++) {
            System.out.printf(COUNT_REPORT_FORMAT,
                              reduce_types[i] + "AllCalls", reduce_counts[i]);
        }
    }
    public void printEffectiveReduceCalls() {
        for (int i = 0; i < reduce_types.length; i++) {
            System.out.printf(COUNT_REPORT_FORMAT,
                              reduce_types[i] + "Calls", reduce_effective_counts[i]);
        }
    }

    public String getAdjList() {
        StringBuilder sb = new StringBuilder();
        sb.append("Adj list: \n");
        for (int i = 0; i < adj.length; i++) {
            sb.append(i);
            sb.append(":");
            for (int j = 0; j < adj[i].length; j++) {
                sb.append(adj[i][j]);
                sb.append(',');
            }
            sb.append("\n");
        }
        return sb.toString();
    }

    public String getArrayContent(int [] arry) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < arry.length; i++) {
            sb.append(arry[i]);
        }
        return sb.toString();
    }

    public String getSolutionString(int [] solution) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < solution.length; i++) {
            if (solution[i] >= 0) {
                sb.append(solution[i]);
            }
            else {
                sb.append('x');
            }
        }
        return sb.toString();
    }

    public String getCurrentSolution() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < curr_solution.length; i++) {
            if (curr_solution[i] >= 0) {
                sb.append(curr_solution[i]);
            }
            else {
                sb.append('x');
            }
        }
        return sb.toString();
    }

    public String getOptimalSolution() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < N; i++) {
            if (optimal_solution[i] >= 0) {
                sb.append(optimal_solution[i]);
            }
            else {
                sb.append('x');
            }
        }
        return sb.toString();
    }

    private int previous_optimum = Integer.MAX_VALUE;

    public void printNode(String label, String status) {
        if ( TRACE <= 0 ) return;
        if (component) {
            label += "c";
        }
        String update_label = " ";
        if ( optimal_value < previous_optimum ) {
            update_label = "$";
            previous_optimum = optimal_value;
        }
        if (TRACE == 1) {
            System.out.format("%4s GUB: %4d %1s, LB: %4d, n = %4d, %-16s | %d\n",
                    label, optimal_value, update_label, lb,
                    remaining_vertices, status, current_value);
        } else if (TRACE == 2) {
            System.out.format("%4s GUB: %4d %1s, LB: %4d, n = %4d, %-16s | %s | %d\n",
                    label, optimal_value, update_label, lb,
                    remaining_vertices, status,
                    solutionToString(curr_solution), current_value);
        }
    }

    public void printLBInfo(LowerBoundType type) {
        if ( TRACE <= 0 ) return;
        if ( type == LowerBoundType.CLIQUE ) {
            if (TRACE > 0) {
                System.out.format("~ max_size = %4d, clique_count = %4d, true_LB = %4d, n = %4d\n",
                        this.CLIQUE_STAT_MAX_CLIQUE_SIZE, this.CLIQUE_STAT_CLIQUE_COUNT, lb - current_value, remaining_vertices);
            }
        }
    }

    // Matching for flow and other things
    FastSet used;

    /**
     * @return current degree of v, with respect to undecided neighbors
     */
    int deg(int v) {
        Debug.check(curr_solution[v] < 0);
        int deg = 0;
        for (int u : adj[v]) {
            if (curr_solution[u] < 0) {
                deg++;
            }
        }
        return deg;
    }

    // compute dv
    double getDV() {
        long start_time = System.nanoTime();
        double sum = 0;
        int totalN = 0;
        for (int i = 0; i < n; i++) {
            if (curr_solution[i] < 0) {
                degTmp[i] = deg(i);
                if (degTmp[i] > 0) {
                    sum += degTmp[i];
                    totalN += 1;
                }
            }
        }

        double mean = sum / totalN;
        double diff_square = 0.0;
        double temp = 0.0;
        for (int i = 0; i < n; i++) {
            if (degTmp[i] > 0) {
                temp = degTmp[i] - mean;
                diff_square += temp * temp;
            }
        }

        double cov = Math.sqrt(1.00 / (totalN - 1.00) * (diff_square)) / mean;
        total_dv_time += (System.nanoTime() - start_time);
        return cov;
    }

    // Compute oc value 
    boolean[] marked, color;
    int oc_count;
    int m;

    void ocDFS(int u) {
        marked[u] = true;
        for (int v : adj[u]) {
            if (curr_solution[v] < -1) {
                m += 1;
                if (!marked[v]) {
                    color[v] = !color[u];
                    ocDFS(v);
                } else if (color[v] == color[u]) {
                    oc_count += 1;
                }
            }
        }
    }

    double getOC() {
        long start_time = System.nanoTime();
        oc_count = 0;
        m = 0;
        for (int i = 0; i < n; i++) {
            marked[i] = false;
            color[i] = false;
        }

        for (int i = 0; i < n; i++) {
            if (curr_solution[i] < -1) {
                if (!marked[i]) {
                    color[i] = true;
                    ocDFS(i);
                }
            }
        }
        total_oc_time += (System.nanoTime() - start_time);
        return (double) 2 * oc_count / m;
    }

    /**
     * @param v the (index of) a vertex
     * @param a the new value for v (1 = in cover, 0 = mot in cover)
     * if a = 0, all neighbors of v must be in the cover; values are set appropriately
     */
    void set(int v, int a) {
        Debug.check(curr_solution[v] < 0);
        current_value += a;
        curr_solution[v] = a;
        restore[--remaining_vertices] = v;
        if (a == 0) {
            for (int u : adj[v]) {
                if (curr_solution[u] < 0) {
                    curr_solution[u] = 1;
                    current_value++;
                    restore[--remaining_vertices] = u;
                    if (DEBUG == 4) {
                        if (component) {
                            System.out.format("Vertex %d, reduced by %s\n",u, red_source);
                        } else {
                            System.out.format("Vertex %d, reduced by %s\n",vertexID[u], red_source);
                        }
                    }
                }
            }
        }
        if (DEBUG == 4) {
            if (component) {
                System.out.format("Vertex %d, reduced by %s\n",v, red_source);
            } else {
                System.out.format("Vertex %d, reduced by %s\n",vertexID[v], red_source);
            }
        }
    }

    /**
     * Generic data structure for all reductions that involve contractions,
     * such as fold2, twin, desk, and funnel
     */
    abstract class Modified {
        /**
         * number of (additional) vertices that will be in a solution as the
         * result of the reduction; in case of an alternative structure,
         * either |A| or |B| vertices will be added to whatever solution is
         * found for the reduced graph; this is useful when computing upper
         * bounds
         */
        int add;
        /**
         * set of vertices removed/replaced by the reduction
         */
        int[] removed;
        /**
         * set of new vertices introduced by the reduction
         */
        int[] vs;
        /**
         * adjacencies among removed vertices before the reduction, so that
         * the reduction can be easily 'undone'
         */
        int[][] oldAdj;

        /**
         * does all the obvious initializations
         */
        Modified(int add, int[] removed, int[] vs, int[][] newAdj) {
            // in case of fold2 involving v with neighbors u_0 and u_1
            //      add = 1
            //      removed = {v, u_1}
            //      vs = neighbors of u_0 and u_1
            //      newAdj[i] = neighbors of vs[i] in the contracted graph
            this.add = add;
            this.removed = removed;
            this.vs = vs;
            oldAdj = new int[vs.length][];
            current_value += add;
            for (int i = 0; i < removed.length; i++) {
                restore[--remaining_vertices] = -1;
            }
            for (int v : removed) {
                Debug.check(curr_solution[v] < 0);
                curr_solution[v] = 2;
            }
            for (int i = 0; i < vs.length; i++) {
                oldAdj[i] = adj[vs[i]];
                adj[vs[i]] = newAdj[i];
            }
        }

        Modified(int[] removed, int[] vs) {
            this.removed = removed;
            this.vs = vs;
        }

        /**
         * restores the <em>graph</em> to its state before the reduction was applied
         */
        void restore() {
            current_value -= add;
            remaining_vertices += removed.length;
            for (int v : removed) {
                curr_solution[v] = -1;
            }
            for (int i = 0; i < vs.length; i++) {
                adj[vs[i]] = oldAdj[i];
                int in_flowV = in_flow[vs[i]], out_flowV = out_flow[vs[i]];
                for (int u : adj[vs[i]]) {
                    if (u == in_flowV) {
                        in_flowV = -1;
                    }
                    if (u == out_flowV) {
                        out_flowV = -1;
                    }
                }
                if (in_flowV >= 0) {
                    out_flow[in_flow[vs[i]]] = -1;
                    in_flow[vs[i]] = -1;
                }
                if (out_flowV >= 0) {
                    in_flow[out_flow[vs[i]]] = -1;
                    out_flow[vs[i]] = -1;
                }
            }
        }

        /**
         * when the reduced graph is solved, reverse() computes the solution
         * with respect to the original graph and updates the global solution
         * vector; this is abstract because the semantics depends on the
         * reduction being performed
         */
        abstract void reverse(int[] curr_solution);

    }

    class Fold extends Modified {

        Fold(int add, int[] removed, int[] vs, int[][] newAdj) {
            super(add, removed, vs, newAdj);
        }

        Fold(int[] removed, int[] vs) {
            super(removed, vs);
        }

        @Override
        void reverse(int[] curr_solution) {
            // in case of fold2 involving v and its neighbors u_0 and u_1,
            // with u_0 and u_1 contracted to w, and w using the index of u_0
            //    removed = {v, u_1}
            //    vs = w and all originally undecided neighbors of u_0 and u_1
            //    curr_solution[i] = status of vs[i]
            int k = removed.length / 2;
            // fold2: if w is not in the solution, include v and exclude u_1,
            // otherwise exclude v and include u_1
            // note that, since w is an alias for u_0, its status is already correct
            if (curr_solution[vs[0]] == 0) {
                for (int i = 0; i < k; i++) {
                    curr_solution[removed[i]] = 1;
                }
                for (int i = 0; i < k; i++) {
                    curr_solution[removed[k + i]] = 0;
                }
            } else if (curr_solution[vs[0]] == 1) {
                for (int i = 0; i < k; i++) {
                    curr_solution[removed[i]] = 0;
                }
                for (int i = 0; i < k; i++) {
                    curr_solution[removed[k + i]] = 1;
                }
            }
        }

    }

    class Alternative extends Modified {

        int k;

        Alternative(int add, int[] removed, int[] vs, int[][] newAdj, int k) {
            super(add, removed, vs, newAdj);
            this.k = k;
        }

        Alternative(int[] removed, int[] vs, int k) {
            super(removed, vs);
            this.k = k;
        }

        @Override
        void reverse(int[] curr_solution) {
            boolean A0 = false, A1 = true;
            boolean B0 = false, B1 = true;
            for (int i = 0; i < k; i++) {
                if (curr_solution[vs[i]] == 0) {
                    A0 = true;
                }
                if (curr_solution[vs[i]] != 1) {
                    A1 = false;
                }
            }
            for (int i = k; i < vs.length; i++) {
                if (curr_solution[vs[i]] == 0) {
                    B0 = true;
                }
                if (curr_solution[vs[i]] != 1) {
                    B1 = false;
                }
            }
            if (A1 || B0) {
                for (int i = 0; i < removed.length / 2; i++) {
                    curr_solution[removed[i]] = 0;
                }
                for (int i = removed.length / 2; i < removed.length; i++) {
                    curr_solution[removed[i]] = 1;
                }
            } else if (B1 || A0) {
                for (int i = 0; i < removed.length / 2; i++) {
                    curr_solution[removed[i]] = 1;
                }
                for (int i = removed.length / 2; i < removed.length; i++) {
                    curr_solution[removed[i]] = 0;
                }
            }
        }

    }

    Modified[] modifieds;
    int modifiedN;

    int[] modTmp;

    /**
     * performs a fold (contraction), eventually creating an instance of Fold
     * @param S the set of vertices whose neighbors are to be contracted
     * @param NS the set of neighbors to be contracted
     */
    void fold(int[] S, int[] NS) {
        Debug.check(NS.length == S.length + 1);
        int[] removed = new int[S.length * 2];
        for (int i = 0; i < S.length; i++) {
            removed[i] = S[i];
        }
        for (int i = 0; i < S.length; i++) {
            removed[S.length + i] = NS[1 + i];
        }
        int s = NS[0];
        // in case of fold2 involving v and neighbors u_0 and u_1
        // removed[0] = v, removed[1] = u_1, s = u_0
        used.clear();
        for (int v : S) {
            used.add(v);
        }
        // fold2: used = {v}
        int[] tmp = modTmp;
        int p = 0;
        for (int v : NS) {
            Debug.check(!used.get(v));
            for ( int u : adj[v] ) {
                if ( curr_solution[u] < 0 && used.add(u) ) {
                    // adds u to tmp only if it's not in used
                    tmp[p++] = u;
                }
            }
        }
        // fold2: tmp = neighbors(u_0) U neighbors(u_1),
        //        used = {v} U neighbors(u_0) U neighbors(u_1)
        //        p = tmp.length
        int[][] newAdj = new int[p + 1][];
        newAdj[0] = copyOf(tmp, p);
        sort(newAdj[0]);
        int[] vs = new int[p + 1];
        vs[0] = s;
        used.clear();
        for (int v : S) {
            used.add(v);
        }
        for (int v : NS) {
            used.add(v);
        }
        // fold2: used = {v, u_0, u_1}, vs[0] = u_0 = s
        //        newAdj[0] = neighbors(u_0) U neighbors(u_1), sorted
        // effectively, we're using u_0 as a placeholder for the new vertex
        for ( int i = 0; i < newAdj[0].length; i++ ) {
            int v = newAdj[0][i];
            p = 0;
            boolean add = false;
            for ( int u : adj[v] ) {
                if ( curr_solution[u] < 0 && ! used.get(u) ) {
                    if ( ! add && s < u ) {
                        // sorting is used to avoid duplication
                        tmp[p++] = s;
                        add = true;
                    }
                    tmp[p++] = u;
                }
            }
            if ( ! add ) {
                tmp[p++] = s;
            }
            vs[1 + i] = v;
            newAdj[1 + i] = copyOf(tmp, p);
        }
        // fold2: undecided neighbors of u_0 and u_1 need to know that they
        // are adjacent to vs[0] and added to vs, so
        //   S = {v}
        //   removed = {v, u_1}
        //   vs[0] = u_0, vs[i], i > 0 is an undecided neighbor of u_0 or u_1
        //   newAdj[i] = neighbors of vs[i], including u_0
        modifieds[modifiedN++] = new Fold(S.length, removed, vs, newAdj);
    }

    void alternative(int[] A, int[] B) {
        Debug.check(A.length == B.length);
        used.clear();
        for (int b : B) {
            for (int u : adj[b]) {
                if (curr_solution[u] < 0) {
                    used.add(u);
                }
            }
        }
        for (int a : A) {
            for (int u : adj[a]) {
                if (curr_solution[u] < 0 && used.get(u)) {
                    set(u, 1);
                }
            }
        }
        int p = 0, q = 0;
        int[] tmp = modTmp;
        used.clear();
        for (int b : B) {
            used.add(b);
        }
        for (int a : A) {
            for (int u : adj[a]) {
                if (curr_solution[u] < 0 && used.add(u)) {
                    tmp[p++] = u;
                }
            }
        }
        int[] A2 = copyOf(tmp, p);
        sort(A2);
        p = 0;
        used.clear();
        for (int a : A) {
            used.add(a);
        }
        for (int b : B) {
            for (int u : adj[b]) {
                if (curr_solution[u] < 0 && used.add(u)) {
                    tmp[p++] = u;
                }
            }
        }
        int[] B2 = copyOf(tmp, p);
        sort(B2);
        int[] removed = new int[A.length + B.length];
        for (int i = 0; i < A.length; i++) {
            removed[i] = A[i];
        }
        for (int i = 0; i < B.length; i++) {
            removed[A.length + i] = B[i];
        }
        int[] vs = new int[A2.length + B2.length];
        for (int i = 0; i < A2.length; i++) {
            vs[i] = A2[i];
        }
        for (int i = 0; i < B2.length; i++) {
            vs[A2.length + i] = B2[i];
        }
        int[][] newAdj = new int[vs.length][];
        used.clear();
        for (int a : A) {
            used.add(a);
        }
        for (int b : B) {
            used.add(b);
        }
        for (int i = 0; i < vs.length; i++) {
            int v = i < A2.length ? A2[i] : B2[i - A2.length];
            int[] C = i < A2.length ? B2 : A2;
            p = q = 0;
            for (int u : adj[v]) {
                if (curr_solution[u] < 0 && !used.get(u)) {
                    while (q < C.length && C[q] <= u) {
                        if (used.get(C[q])) {
                            q++;
                        } else {
                            tmp[p++] = C[q++];
                        }
                    }
                    if (p == 0 || tmp[p - 1] != u) {
                        tmp[p++] = u;
                    }
                }
            }
            while (q < C.length) {
                if (used.get(C[q])) {
                    q++;
                } else {
                    tmp[p++] = C[q++];
                }
            }
            newAdj[i] = copyOf(tmp, p);
        }
        modifieds[modifiedN++] = new Alternative(removed.length / 2, removed, vs, newAdj, A2.length);
    }

    void restore(int n) {
        while (remaining_vertices < n) {
            int v = restore[remaining_vertices];
            if (v >= 0) {
                current_value -= curr_solution[v];
                curr_solution[v] = -1;
                remaining_vertices++;
            } else {
                modifieds[--modifiedN].restore();
            }
        }
    }

    void reverse() {
        for (int i = modifiedN - 1; i >= 0; i--) {
            modifieds[i].reverse(optimal_solution);
        }
    }

    // Flow related
    int[] que, level, iter;

    boolean dinicDFS(int v) {
        while (iter[v] >= 0) {
            int u = adj[v][iter[v]--], w = in_flow[u];
            if (curr_solution[u] >= 0) {
                continue;
            }
            if (w < 0 || level[v] < level[w] && iter[w] >= 0 && dinicDFS(w)) {
                in_flow[u] = v;
                out_flow[v] = u;
                return true;
            }
        }
        return false;
    }

    /*
     * Computes maximum matching/flow in LR graph. 
     * Using Hopcroft-Karp/Dinic max. flow
     */
    void updateLP() {
        try (Stat stat = new Stat("updateLP")) {
            for (int v = 0; v < n; v++) {
                // There's flow going out of v and (v is undecided XOR where v puts flow is undecided)
                if (out_flow[v] >= 0 && ((curr_solution[v] < 0) ^ (curr_solution[out_flow[v]] < 0))) {
                    // Reset v's outgoing flow
                    in_flow[out_flow[v]] = -1;
                    out_flow[v] = -1;
                }
            }
            for (;;) {
                used.clear();
                // Initialize levels
                int qs = 0, qt = 0;
                for (int v = 0; v < n; v++) {
                    // v is undecided and there's no flow going out of v
                    if (curr_solution[v] < 0 && out_flow[v] < 0) {
                        level[v] = 0;
                        used.add(v);
                        que[qt++] = v;
                    }
                }
                boolean ok = false;
                // BFS to create level graph
                while (qs < qt) {
                    // Remove first element in queue
                    int v = que[qs++];
                    iter[v] = adj[v].length - 1;
                    // Go through v's neighbors (labeled u)
                    for (int u : adj[v]) {
                        // u is undecided and n+u (ru) is not already used
                        if (curr_solution[u] < 0 && used.add(n + u)) {
                            int w = in_flow[u];
                            // There's no flow coming into u (found a blocking flow)
                            if (w < 0) {
                                ok = true;
                                // u has flow coming in from w
                            } else {
                                level[w] = level[v] + 1;
                                used.add(w);
                                que[qt++] = w;
                            }
                        }
                    }
                }
                // No more augmenting paths 
                if (!ok) {
                    break;
                }
                // Push flow through 
                for (int v = n - 1; v >= 0; v--) {
                    // v is undecided and there's no outgoing flow from v
                    if (curr_solution[v] < 0 && out_flow[v] < 0) {
                        // Push flow through
                        dinicDFS(v);
                    }
                }
            }
        }
    }

    boolean lpReduction() {
        red_source = VERTEX_LP_STRING;

        long start_time = System.nanoTime();
        int oldn = remaining_vertices;

        updateLP();

        if (DEBUG == 3) {
            System.out.format("lp reduction -> Before: %s\n", getCurrentSolution());
        }

        try (Stat stat = new Stat("reduce_LP")) {
            // Here used = maximum matching/flow ?
            for (int v = 0; v < n; v++) {
                // l_v in matching and r_v not in matching
                if (curr_solution[v] < 0 && used.get(v) && !used.get(n + v)) {
                    set(v, 0);
                }
            }

            // used = ???
            used.clear();
            int p = 0;
            fill(iter, 0);
            for (int s = 0; s < n; s++) {
                // s is undecided and s not already in used
                if (curr_solution[s] < 0 && used.add(s)) {
                    int qt = 0;
                    que[qt] = s;
                    while (qt >= 0) {
                        int v = que[qt], u = -1;
                        // v is a left vertex
                        if (v < n) {
                            while (iter[v] < adj[v].length) {
                                u = n + adj[v][iter[v]++]; // get r_u
                                // u is undecided and r_u i in not already in used
                                if (curr_solution[u - n] < 0 && used.add(u)) {
                                    break;
                                }
                                u = -1;
                            }
                            // if edge l_x, r_v is in used, then x = u
                            // i.e. the edge of the matching with endpoint r_v is in used
                        } else if (used.add(in_flow[v - n])) {
                            u = in_flow[v - n];
                        }
                        // if u is a valid vertex in the LR graph
                        if (u >= 0) {
                            que[++qt] = u;
                        } else {
                            level[p++] = v;
                            qt--;
                        }
                    }
                }
            }

            // used = ???
            used.clear();
            for (int i = p - 1; i >= 0; i--) {
                if (used.add(level[i])) {
                    int v = level[i];
                    int qs = 0, qt = 0;
                    que[qt++] = v;
                    boolean ok = true;
                    while (qs < qt) {
                        v = que[qs++];
                        if (used.get(v >= n ? (v - n) : (v + n))) {
                            ok = false;
                        }
                        if (v >= n) {
                            for (int u : adj[v - n]) {
                                if (curr_solution[u] < 0 && used.add(u)) {
                                    que[qt++] = u;
                                }
                            }
                        } else if (used.add(n + out_flow[v])) {
                            que[qt++] = n + out_flow[v];
                        }
                    }

                    //ok = false; // @TODO:should this be here?, is this a mistake? Commented out for now

                    if (ok) {
                        for (int j = 0; j < qt; j++) {
                            v = que[j];
                            if (v >= n) {
                                set(v - n, 0);
                            }
                        }
                    }
                }
            }
        }

        if (DEBUG >= 3 && depth <= maxDepth && oldn != remaining_vertices) {
            debug("LP: %d -> %d%n", oldn, remaining_vertices);
        }
        if (oldn != remaining_vertices) {
            Stat.count("reduceN_lp", oldn - remaining_vertices);
        }
        if (DEBUG == 3) {
            System.out.format("lp reduction ->  After: %s\n", getCurrentSolution());
        }
        long end_time = System.nanoTime();
        lpTime += (end_time - start_time);
        return oldn != remaining_vertices;
    }

    boolean deg1Reduction() {
        try (Stat stat = new Stat("reduce_deg1")) {
            if (DEBUG == 3) {
                System.out.format("deg1 reduction -> Before: %s\n", getCurrentSolution());
            }

            red_source = VERTEX_DEG1_STRING;

            long start_time = System.nanoTime();
            int oldn = remaining_vertices;
            int[] deg = iter;
            int qt = 0;
            used.clear();
            int edges = 0;
            for (int v = 0; v < n; v++) {
                if (curr_solution[v] < 0) {
                    // if all vertices are undecided use length of original
                    // adjacency list, else compute the current
                    deg[v] = n == remaining_vertices ? adj[v].length : deg(v);
                    edges += deg[v];
                    if (deg[v] <= 1) {
                        que[qt++] = v;
                        used.add(v);
                    }
                }
            }

            while (qt > 0) {
                int v = que[--qt];
                if (curr_solution[v] >= 0) {
                    continue;
                }
                Debug.check(deg[v] <= 1);
                for (int u : adj[v]) {
                    if (curr_solution[u] < 0) {
                        for (int w : adj[u]) {
                            if (curr_solution[w] < 0) {
                                deg[w]--;
                                edges -= 2;
                                if (deg[w] <= 1 && used.add(w)) {
                                    que[qt++] = w;
                                }
                            }
                        }
                    }
                }
                set(v, 0);
            }
            if (DEBUG >= 3 && depth <= maxDepth && oldn != remaining_vertices) {
                debug("deg1: %d -> %d%n", oldn, remaining_vertices);
            }
            if (oldn != remaining_vertices) {
                Stat.count("reduceN_deg1", oldn - remaining_vertices);
            }
            if (DEBUG == 3) {
                System.out.format("deg1 reduction ->  After: %s\n", getCurrentSolution());
            }
            long end_time = System.nanoTime();
            degTime += (end_time - start_time);
            density = edges / (double) (remaining_vertices * (remaining_vertices - 1));
            return oldn != remaining_vertices;
        }
    }

    boolean dominateReduction() {
        try (Stat stat = new Stat("reduce_dominate")) {
            if (DEBUG == 3) {
                System.out.format("dom reduction -> Before: %s\n", getCurrentSolution());
            }

            red_source = VERTEX_DOM_STRING;

            long start_time = System.nanoTime();
            int oldn = remaining_vertices;
            for (int v = 0; v < n; v++) {
                if (curr_solution[v] < 0) {
                    used.clear();
                    used.add(v);
                    for (int u : adj[v]) {
                        if (curr_solution[u] < 0) {
                            used.add(u);
                        }
                    }
loop : 
                    for (int u : adj[v]) {
                        if (curr_solution[u] < 0) {
                            for (int w : adj[u]) {
                                if (curr_solution[w] < 0 && !used.get(w)) {
                                    continue loop;
                                }
                            }
                            set(v, 1);
                            break;
                        }
                    } // end loop
                }
            }
            if (DEBUG >= 3 && depth <= maxDepth && oldn != remaining_vertices) {
                debug("dominate: %d -> %d%n", oldn, remaining_vertices);
            }
            if (oldn != remaining_vertices) {
                Stat.count("reduceN_dom", oldn - remaining_vertices);
            }
            if (DEBUG == 3) {
                System.out.format("dom reduction ->  After: %s\n", getCurrentSolution());
            }
            long end_time = System.nanoTime();
            domTime += (end_time - start_time);
            return oldn != remaining_vertices;
        }
    }

    /**
     * performs all possible fold2 reductions; if the neighbors of any
     * degree-2 vertex are adjacent, a dominance reduction takes place instead
     */
    boolean fold2Reduction() {
        try (Stat stat = new Stat("reduce_fold2")) {
            if (DEBUG == 3) {
                System.out.format("fold2 reduction -> Before: %s\n", getCurrentSolution());
            }

            red_source = VERTEX_FOLD2_STRING;

            long start_time = System.nanoTime();
            int oldn = remaining_vertices;
            int[] tmp = level;
            int num_folded = 0;

            loop : 
            for (int v = 0; v < n; v++) {
                if (curr_solution[v] < 0) {
                    int p = 0;
                    for (int u : adj[v]) { // Check if deg(v) = 2
                        if (curr_solution[u] < 0) {
                            tmp[p++] = u;
                            if (p > 2) {
                                continue loop;
                            }
                        }
                    }
                    if (p < 2) {
                        continue;
                    }
                    // the neighbors of v are tmp[0] and tmp[1]
                    for (int u : adj[tmp[0]]) {
                        // if v's neighbors are connected, both of them
                        // dominate v and we can exclude v from the cover
                        if (u == tmp[1]) {
                            set(v, 0);
                            continue loop;
                        }
                    }
                    fold(new int[]{v}, copyOf(tmp, 2));
                    num_folded += 3;
                }
            } // end loop

            if (DEBUG >= 3 && depth <= maxDepth && oldn != remaining_vertices) {
                debug("fold2: %d -> %d%n", oldn, remaining_vertices);
            }
            if (oldn != remaining_vertices) {
                Stat.count("reduceN_fold2", oldn - remaining_vertices + num_folded);
            }
            if (DEBUG == 3) {
                System.out.format("fold2 reduction ->  After: %s\n", getCurrentSolution());
            }
            long end_time = System.nanoTime();
            foldTime += (end_time - start_time);
            return oldn != remaining_vertices;
        }
    }

    boolean twinReduction() {
        try (Stat stat = new Stat("reduce_twin")) {
            if (DEBUG == 3) {
                System.out.format("twin reduction -> Before: %s\n", getCurrentSolution());
            }

            red_source = VERTEX_TWIN_STRING;

            long start_time = System.nanoTime();
            int oldn = remaining_vertices;
            int num_folded = 0;
            int[] used = iter;
            int uid = 0;
            int[] NS = new int[3];
            for (int i = 0; i < n; i++) {
                used[i] = 0;
            }
loop : 
            for (int v = 0; v < n; v++) { 
                // used[i] = mark of i
                if (curr_solution[v] < 0 && deg(v) == 3) { 
                    int p = 0;
                    for (int u : adj[v]) {
                        // To see if v is apart of a twin: (assuming v has degree 3)
                        // For each neighbor, w, of N(v), mark each with the the value of |{wx for x in N(v)}|
                        // Mark v's neighbor's with a 4
                        // If N(v) is disjoint, then any vertex, w, with a mark of 3 and degree 3, is a twin of v
                        if (curr_solution[u] < 0) {
                            NS[p++] = u;
                            uid++;
                            for (int w : adj[u]) {
                                if (curr_solution[w] < 0 && w != v) {
                                    if (p == 1) {
                                        used[w] = uid;
                                    } else if (used[w] == uid - 1) {
                                        used[w]++;
                                        if (p == 3 && deg(w) == 3) {
                                            uid++; 
                                            for (int z : NS) {
                                                used[z] = uid;
                                            }
                                            boolean ind = true;
                                            for (int z : NS) {
                                                for (int a : adj[z]) { //|adj[z]| == 3
                                                    if (curr_solution[a] < 0 && used[a] == uid) {
                                                        ind = false;
                                                    }
                                                }
                                            }
                                            if (ind) {
                                                fold(new int[]{v, w}, NS.clone());
                                                num_folded += 5;
                                            } else {
                                                set(v, 0);
                                                set(w, 0);
                                            }
                                            continue loop;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if (DEBUG >= 3 && depth <= maxDepth && oldn != remaining_vertices) {
                debug("twin: %d -> %d%n", oldn, remaining_vertices);
            }
            if (oldn != remaining_vertices) {
                Stat.count("reduceN_twin", oldn - remaining_vertices + num_folded);
            }
            if (DEBUG == 3) {
                System.out.format("twin reduction ->  After: %s\n", getCurrentSolution());
            }
            long end_time = System.nanoTime();
            twinTime += (end_time - start_time);
            return oldn != remaining_vertices;
        }
    }

    boolean funnelReduction() {
        try (Stat stat = new Stat("reduce_alternative")) {
            if (DEBUG == 3) {
                System.out.format("funnel reduction -> Before: %s\n", getCurrentSolution());
            }

            red_source = VERTEX_FUNNEL_STRING;

            long start_time = System.nanoTime();
            int oldn = remaining_vertices;
            int num_folded = 0;
loop : 
            for (int v = 0; v < n; v++) {
                // Goal: find a u in N(v) such that u and v form a funnel
                if (curr_solution[v] < 0) {
                    used.clear();
                    int[] tmp = level;
                    int p = 0;
                    for (int u : adj[v]) {
                        if (curr_solution[u] < 0 && used.add(u)) {
                            tmp[p++] = u;
                        }
                    }

                    // tmp = N(v)
                    // p = |N(v)|
                    if (p <= 1) {
                        set(v, 0);
                        continue;
                    }
                    // find a possible candidate for u, u1
                    int u1 = -1;
                    for (int i = 0; i < p; i++) {
                        int d = 0;
                        for (int u : adj[tmp[i]]) { // get number of edges between u and other neighbors of v
                            if (curr_solution[u] < 0 && used.get(u)) {
                                d++;
                            }
                        }
                        if (d + 1 < p) { // v's neighbor is a possible candidate
                            u1 = tmp[i];
                            break;
                        }
                    }
                    if (u1 < 0) {
                        set(v, 0);
                        continue;
                    } else {
                        int[] id = iter;
                        for (int i = 0; i < p; i++) {
                            id[tmp[i]] = -1;
                        }
                        for (int u : adj[u1]) {
                            if (curr_solution[u] < 0) { // mark u1's neighbors with 0
                                id[u] = 0;
                            }
                        }
                        int u2 = -1;
                        for (int i = 0; i < p; i++) {
                            if (tmp[i] != u1 && id[tmp[i]] < 0) { // tmp[i] is not connected to u1
                                u2 = tmp[i];
                                break;
                            }
                        }
                        Debug.check(u2 >= 0);
                        used.remove(u1);
                        used.remove(u2);
                        // used = N(v) - {u1, u2}
                        int d1 = 0, d2 = 0;
                        for (int w : adj[u1]) {
                            if (curr_solution[w] < 0 && used.get(w)) {
                                d1++;
                            }
                        }
                        for (int w : adj[u2]) {
                            if (curr_solution[w] < 0 && used.get(w)) {
                                d2++;
                            }
                        }
                        // dx = |N(v) interset N(ux)|
                        if (d1 < p - 2 && d2 < p - 2) { // both u1, and u2 are invalid candidates (there is some neighbor of v that that u1 is not connected to, similar for u2)
                            continue;
                        }
                        for (int i = 0; i < p; i++) {
                            int u = tmp[i];
                            if (u == u1 || u == u2) {
                                continue;
                            }
                            int d = 0;
                            for (int w : adj[u]) {
                                if (curr_solution[w] < 0 && used.get(w)) {
                                    d++;
                                }
                            }
                            if (d < p - 3) { // there is a neighbor that's not u1 or u2 that is not connected to another neighbor i.e. v's neighbor doesn't form a clique
                                continue loop;
                            }
                        }
                        int u = (d1 == p - 2) ? u2 : u1; // one of u1 or u2 formms a funnel with v
                        alternative(new int[]{v}, new int[]{u});
                        num_folded += 2;
                    }
                }
            }
            if (DEBUG >= 3 && depth <= maxDepth && oldn != remaining_vertices) {
                debug("funnel: %d -> %d%n", oldn, remaining_vertices);
            }
            if (oldn != remaining_vertices) {
                Stat.count("reduceN_funnel", oldn - remaining_vertices);
            }
            if (DEBUG == 3) {
                System.out.format("funnel reduction ->  After: %s\n", getCurrentSolution());
            }
            long end_time = System.nanoTime();
            funnelTime += (end_time - start_time);
            return oldn != remaining_vertices;
        }
    }

    boolean deskReduction() {
        try (Stat stat = new Stat("reduce_desk")) {
            if (DEBUG == 3) {
                System.out.format("desk reduction -> Before: %s\n", getCurrentSolution());
            }

            red_source = VERTEX_DESK_STRING;

            long start_time = System.nanoTime();
            int oldn = remaining_vertices;
            int num_folded = 0;
            int[] tmp = level;
            int[] nv = iter;
            for (int i = 0; i < n; i++) {
                nv[i] = -1;
            }
loop : 
            //nv[i] = preceding vertex in cycle
            for (int v = 0; v < n; v++) {
                if (curr_solution[v] < 0) {
                    int d = 0;
                    // Get degree of v
                    for (int u : adj[v]) {
                        if (curr_solution[u] < 0) {
                            tmp[d++] = u;
                            nv[u] = v;
                            if (d > 4) {
                                break;
                            }
                        }
                    }
                    if (d == 3 || d == 4) {
                        int d2 = 0;
                        for (int i = 0; i < d; i++) {
                            int a = deg(tmp[i]);
                            if (a == 3 || a == 4) {
                                tmp[d2++] = tmp[i];
                            }
                        }
                        for (int i = 0; i < d2; i++) { // O(constant)
                            int u1 = tmp[i];
                            int sB1 = 0;
                            used.clear();
                            for (int w : adj[u1]) {
                                if (curr_solution[w] < 0 && w != v) {
                                    used.add(w);
                                    sB1++;
                                }
                            }
                            for (int j = i + 1; j < d2; j++) {
                                int u2 = tmp[j];
                                if (used.get(u2)) {
                                    continue;
                                }
                                int sB2 = 0;
                                for (int w : adj[u2]) {
                                    if (curr_solution[w] < 0 && w != v && !used.get(w)) {
                                        sB2++;
                                    }
                                }
                                if (sB1 + sB2 <= 3) {
                                    for (int w : adj[u2]) {
                                        if (curr_solution[w] < 0 && used.get(w) && nv[w] != v) {
                                            int d3 = deg(w);
                                            if (d3 == 3 || d3 == 4) {
                                                int sA = d - 2;
                                                for (int z : adj[w]) {
                                                    if (curr_solution[z] < 0 && z != u1 && z != u2 && nv[z] != v) {
                                                        sA++;
                                                    }
                                                }
                                                if (sA <= 2) {
                                                    alternative(new int[]{v, w}, new int[]{u1, u2});
                                                    num_folded += 4;
                                                    continue loop;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if (DEBUG >= 3 && depth <= maxDepth && oldn != remaining_vertices) {
                debug("desk: %d -> %d%n", oldn, remaining_vertices);
            }
            if (oldn != remaining_vertices) {
                Stat.count("reduceN_desk", oldn - remaining_vertices + num_folded);
            }
            if (DEBUG == 3) {
                System.out.format("desk reduction ->  After: %s\n", getCurrentSolution());
            }
            long end_time = System.nanoTime();
            deskTime += (end_time - start_time);
            return oldn != remaining_vertices;
        }
    }

    boolean unconfinedReduction() {
        try (Stat stat = new Stat("reduce_unconfined")) {
            if (DEBUG == 3) {
                System.out.format("unconfined reduction -> Before: %s\n", getCurrentSolution());
            }

            long start_time = System.nanoTime();
            int oldn = remaining_vertices;
            int[] NS = level, deg = iter;
            for (int v = 0; v < n; v++) {
                if (curr_solution[v] < 0) {
                    used.clear();
                    used.add(v);
                    int p = 1, size = 0;
                    for (int u : adj[v]) {
                        if (curr_solution[u] < 0) {
                            used.add(u);
                            NS[size++] = u;
                            deg[u] = 1;
                        }
                    }
                    boolean ok = false;
                    red_source = VERTEX_UNCONFINED_STRING;
loop : 
                    while (!ok) {
                        // used = S
                        // deg[i] = |N(i) - Sv|
                        ok = true;
                        for (int i = 0; i < size; i++) {
                            // Check if u is a unique child
                            int u = NS[i];
                            if (deg[u] != 1) { // u is not a unique child 
                                continue;
                            }
                            int z = -1;
                            for (int w : adj[u]) {
                                if (curr_solution[w] < 0 && !used.get(w)) { 
                                    if (z >= 0) { // |N(u) - N[S]| == 2
                                        z = -2;
                                        break;
                                    }
                                    z = w;
                                }
                            }
                            if (z == -1) { // |N(u) - N[Sv]| = 0, v is unconfined
                                if (PACKING_REDUCTION) {
                                    long packing_start_time = System.nanoTime();
                                    int[] qs = que;
                                    int q = 0;
                                    qs[q++] = 1;
                                    for (int w : adj[v]) {
                                        if (curr_solution[w] < 0) {
                                            qs[q++] = w;
                                        }
                                    }
                                    packing.add(copyOf(qs, q));
                                    long packing_end_time = System.nanoTime();
                                    packingTime += packing_end_time - packing_start_time;
                                }
                                set(v, 1);
                                break loop;
                            } else if (z >= 0) { // N(u) - N[Sv] = {z} 
                                ok = false;
                                used.add(z);
                                p++;
                                for (int w : adj[z]) {
                                    if (curr_solution[w] < 0) {
                                        if (used.add(w)) { // Add w to Sv
                                            NS[size++] = w;
                                            deg[w] = 1;
                                        } else {
                                            deg[w]++;
                                        }
                                    }
                                }
                            }
                        }
                    }
                    if (curr_solution[v] < 0 && p >= 2) {
                        used.clear();
                        for (int i = 0; i < size; i++) {
                            used.add(NS[i]);
                        }
                        int[] vs = que;
                        for (int i = 0; i < size; i++) {
                            vs[i] = vs[n + i] = -1;
                            int u = NS[i];
                            if (deg[u] != 2) {
                                continue;
                            }
                            int v1 = -1, v2 = -1;
                            for (int w : adj[u]) {
                                if (curr_solution[w] < 0 && !used.get(w)) {
                                    if (v1 < 0) {
                                        v1 = w;
                                    } else if (v2 < 0) {
                                        v2 = w;
                                    } else {
                                        v1 = v2 = -1;
                                        break;
                                    }
                                }
                            }
                            if (v1 > v2) {
                                int t = v1;
                                v1 = v2;
                                v2 = t;
                            }
                            vs[i] = v1;
                            vs[n + i] = v2;
                        }
                        red_source = "unconfined_diamond";
loop : 
                        for (int i = 0; i < size; i++) {
                            if (vs[i] >= 0 && vs[n + i] >= 0) {
                                int u = NS[i];
                                used.clear();
                                for (int w : adj[u]) {
                                    if (curr_solution[w] < 0) {
                                        used.add(w);
                                    }
                                }
                                for (int j = i + 1; j < size; j++) {
                                    if (vs[i] == vs[j] && vs[n + i] == vs[n + j] && !used.get(NS[j])) {
                                        if (PACKING_REDUCTION) {
                                            long packing_start_time = System.nanoTime();
                                            int[] qs = que;
                                            int q = 0;
                                            qs[q++] = 1;
                                            for (int w : adj[v]) {
                                                if (curr_solution[w] < 0) {
                                                    qs[q++] = w;
                                                }
                                            }
                                            packing.add(copyOf(qs, q));
                                            long packing_end_time = System.nanoTime();
                                            packingTime += packing_end_time - packing_start_time;
                                        }
                                        
                                        set(v, 1);
                                        Stat.count("reduceN_diamond");
                                        break loop;
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if (DEBUG >= 3 && depth <= maxDepth && oldn != remaining_vertices) {
                debug("unconfined: %d -> %d%n", oldn, remaining_vertices);
            }
            if (oldn != remaining_vertices) {
                Stat.count("reduceN_unconfined", oldn - remaining_vertices);
            }
            if (DEBUG == 3) {
                System.out.format("unconfined reduction ->  After: %s\n", getCurrentSolution());
            }
            long end_time = System.nanoTime();
            unconfinedTime += (end_time - start_time);
            return oldn != remaining_vertices;
        }
    }

    // Returns 1 if graph is reduced, 0 otherwise. -1 for ???
    int packingReduction() {
        try (Stat stat = new Stat("reduce_packing")) {
            long start_time = System.nanoTime();
            if (DEBUG == 3) {
                System.out.format("packing reduction -> Before: %s\n", getCurrentSolution());
            }
            int oldn = remaining_vertices;
            int[] curr_solution2 = curr_solution.clone();
            int a = -1;
            for (int i = 0; i < packing.size(); i++) {
                if (a != remaining_vertices) {
                    for (int j = 0; j < N; j++) {
                        curr_solution2[j] = curr_solution[j];
                    }
                    for (int j = modifiedN - 1; j >= 0; j--) {
                        modifieds[j].reverse(curr_solution2);
                    }
                    a = remaining_vertices;
                }
                int[] ps = packing.get(i);
                int max = ps.length - 1 - ps[0], sum = 0, size = 0;
                int[] S = level;
                for (int j = 1; j < ps.length; j++) {
                    int v = ps[j];
                    if (curr_solution2[v] < 0) {
                        S[size++] = v;
                    }
                    if (curr_solution2[v] == 1) {
                        sum++;
                    }
                }
                if (sum > max) {
                    Stat.count("reduceN_packingR");
                    long end_time = System.nanoTime();
                    packingTime += end_time - start_time;
                    return -1;
                } else if (sum == max && size > 0) {
                    int[] count = iter;
                    used.clear();
                    for (int j = 0; j < size; j++) {
                        used.add(S[j]);
                        count[S[j]] = -1;
                    }
                    for (int j = 0; j < size; j++) {
                        for (int u : adj[S[j]]) {
                            if (curr_solution[u] < 0) {
                                if (used.add(u)) {
                                    count[u] = 1;
                                } else if (count[u] < 0) {
                                    long end_time = System.nanoTime();
                                    packingTime += end_time - start_time;
                                    return -1;
                                } else {
                                    count[u]++;
                                }
                            }
                        }
                    }
                    for (int j = 0; j < size; j++) {
                        for (int u : adj[S[j]]) {
                            if (curr_solution[u] < 0 && count[u] == 1) {
                                int[] tmp = que;
                                int p = 0;
                                tmp[p++] = 1;
                                for (int w : adj[u]) {
                                    if (curr_solution[w] < 0 && !used.get(w)) {
                                        tmp[p++] = w;
                                    }
                                }
                                packing.add(copyOf(tmp, p));
                            }
                        }
                    }
                    for (int j = 0; j < size; j++) {
                        if (S[j] == 1) {
                            long end_time = System.nanoTime();
                            packingTime += end_time - start_time;
                            return -1;
                        }
                        Debug.check(curr_solution[S[j]] < 0);
                        set(S[j], 0);
                    }
                } else if (sum + size > max) {
                    Debug.check(size >= 2);
                    used.clear();
                    for (int j = 0; j < size; j++) {
                        used.add(S[j]);
                    }
                    for (int v : adj[S[0]]) {
                        if (curr_solution[v] < 0 && !used.get(v)) {
                            int p = 0;
                            for (int u : adj[v]) {
                                if (used.get(u)) p++;
                            }
                            if (sum + p > max) {
                                int[] qs = que;
                                int q = 0;
                                qs[q++] = 2;
                                for (int u : adj[v]) {
                                    if (curr_solution[u] < 0) {
                                        qs[q++] = u;
                                    }
                                }
                                packing.add(copyOf(qs, q));
                                set(v, 1);
                                break;
                            }
                        }
                    }
                }
            }
            if (DEBUG >= 3 && depth <= maxDepth && oldn != remaining_vertices) {
                debug("packing: %d -> %d%n", oldn, remaining_vertices);
            }
            if (oldn != remaining_vertices) {
                Stat.count("reduceN_packing", oldn - remaining_vertices);
            }
            if (DEBUG == 3) {
                System.out.format("packing reduction ->  After: %s\n", getCurrentSolution());
            }
            long end_time = System.nanoTime();
            packingTime += end_time - start_time;
            return oldn != remaining_vertices ? 1 : 0;
        } // end, try block (no catch)
    } // packingReduction

    void branching() {
        int oldLB = lb;
        LowerBoundType oldLBType = lbType;
        int v = -1, v_degree = 0;
        int[] mirrors = que;
        int mirrorN = 0;
        if (DEBUG >= 2) {
            debug("%-20s (%d): %s, %s\n", "Before branching", depth, getOptimalSolution(), getCurrentSolution());
        }

        try (Stat stat = new Stat("branching")) {
            // pick branching vertex v
            if (BRANCHING == 0) {
                // Random branching
                int p = rand.nextInt(remaining_vertices);
                for (int i = 0; i < n; i++) {
                    if (curr_solution[i] < 0 && p-- == 0) {
                        v = i;
                    }
                }
                v_degree = deg(v);
            } else if (BRANCHING == 1) {
                // Min degree branching
                v_degree = n + 1;
                for (int u = 0; u < n; u++) {
                    if (curr_solution[u] < 0) {
                        int deg = deg(u);
                        if (v_degree > deg) {
                            v = u;
                            v_degree = deg;
                        }
                    }
                }
            } else if (BRANCHING == 2) {
                // Max degree branching
                v_degree = -1;
                long minE = 0;
                for (int u = 0; u < n; u++) {
                    if (curr_solution[u] < 0) {
                        int deg = deg(u);
                        if (v_degree > deg) continue;
                        long e = 0;
                        used.clear();
                        for (int w : adj[u]) {
                            if (curr_solution[w] < 0) {
                                used.add(w);
                            }
                        }
                        for (int w : adj[u]) {
                            if (curr_solution[w] < 0) {
                                for (int w2 : adj[w]) {
                                    if (curr_solution[w2] < 0 && used.get(w2)) {
                                        e++;
                                    }
                                }
                            }
                        }
                        if (v_degree < deg || v_degree == deg && minE > e) {
                            v_degree = deg;
                            minE = e;
                            v = u;
                        }
                    }
                }
            } // end pick branching vertex

            int[] ps = iter;
            for (int i = 0; i < n; i++) 
                ps[i] = -2;
            used.clear();
            used.add(v);

            // Mark undecided neighbors of v
            for (int u : adj[v]) {
                if (curr_solution[u] < 0) {
                    used.add(u);
                    ps[u] = -1;
                }
            }

            // Check for mirrors
            for (int u : adj[v]) {
                if (curr_solution[u] < 0) {
                    for (int w : adj[u]) {
                        if (curr_solution[w] < 0 && used.add(w)) {
                            int c1 = v_degree; // Number of v's neighbors that aren't also neighbors of w
                            // Make ps = N(v) \ N(w)
                            for (int z : adj[w]) {
                                // ps[z] != -2 means it is an undecided neighbor of v
                                if (curr_solution[z] < 0 && ps[z] != -2) {
                                    ps[z] = w;
                                    c1--;
                                }
                            }
                            boolean ok = true;
                            for (int u2 : adj[v]) {
                                if (curr_solution[u2] < 0 && ps[u2] != w) {
                                    // u2 is in N(v) \ N(w)
                                    int c2 = 0; // number of u2's neighbors that are also w's neighbors
                                    for (int w2 : adj[u2]) {
                                        if (curr_solution[w2] < 0 && ps[w2] == w) {
                                            c2++;
                                        }
                                    }
                                    if (c2 != c1 - 1) {
                                        // if c2 != c1 - 1 that means that N(v) \ N(w) is not a clique and non-empty
                                        ok = false;
                                        break;
                                    }
                                }
                            }
                            if (ok) mirrors[mirrorN++] = w;
                        }
                    }
                }
            }
            if (DEBUG >= 2) {
                debug("PS and Mirror things\n");
                debug("Current solution: %s\n", getCurrentSolution());
                debug("PS content: %s\n", getArrayContent(ps));
                debug("Mirrors: %s\n", getArrayContent(mirrors));
            }
        }

        int pn = remaining_vertices;
        int oldP = packing.size();

        if (DEBUG >= 2) {
            debug("Parent depth: %d\n", depth);
            debug("branching vertex: %d\n", v);
        }

        // Update packing constraints
        if (PACKING_REDUCTION) {
            int[] tmp = level;
            int p = 0;
            tmp[p++] = mirrorN > 0 ? 2 : 1;
            for (int u : adj[v]) {
                if (curr_solution[u] < 0) {
                    tmp[p++] = u;
                }
            }
            packing.add(copyOf(tmp, p));
        }

        if (TRACE > 0 && TRACE < 3) {
            System.out.format(" /\\ branching_vertex:   * %d\n", vertexID[v]);
        }
        // Set branching vertex as in the cover
        set(v, 1);
        for (int i = 0; i < mirrorN; i++) {
            set(mirrors[i], 1);
        }
        if (DEBUG >= 2 && depth <= maxDepth) {
            if (mirrorN > 0) {
                debug("branchMirror (%d, %d): 1%n", v_degree, mirrorN);
            } else {
                debug("branch (%d): 1%n", v_degree);
            }
        }
        depth++;
        if (DEBUG >= 1) {
            debug("Performing rec on left child\n");
            //debug("Depth: %d\n", depth);
        }
        // nBranchings++; // see rec()
        // process left child
        rec("= 1");
        if (TRACE > 0 && TRACE < 3) {
            System.out.format(" __ left_branch_done:   * %d\n", vertexID[v]);
        }

        // Restore node to before solving left child
        while (packing.size() > oldP) {
            packing.remove(packing.size() - 1);
        }
        lb = oldLB;
        lbType = oldLBType;
        depth--;
        restore(pn);
        if (DEBUG >= 2) {
            debug("%-20s (%d): %s, %s\n", "Restoring", depth, getOptimalSolution(), getCurrentSolution());
        }
        if ( lb >= optimal_value ) {
            incrementLBCount(lbType);
            nLeftCuts += 1;
            if (DEBUG >= 1) {
                debug("break at left child\n");
            }
            return;
        }
        // not clear why this gets incremented here instead of a more obvious
        // place, but that's what Iwata did
        nBranchings++;
        if (mirrorN == 0) {
            used.clear();
            // make used = N[v]
            used.add(v);
            for (int u : adj[v]) {
                if (curr_solution[u] < 0) {
                    used.add(u);
                }
            }
            // used = N[v]
            if (PACKING_REDUCTION) {
                int[] ws = new int[n];
                fill(ws, -1);
                // Here u = 'w' from the paper
                for (int u : adj[v]) {
                    if (curr_solution[u] < 0) {
                        // make tmp = N('w') from paper (here 'w' = u)
                        int[] tmp = level;
                        int p = 0;
                        tmp[p++] = 1;
                        for (int w : adj[u]) {
                            if (curr_solution[w] < 0 && !used.get(w)) {
                                tmp[p++] = w;
                                ws[w] = u;
                            }
                        }
                        // If p < 2, then that means N('w') \ N[v] is empty
                        Debug.check(p >= 2);

                        // Not sure if the below fixes it or is correct
                        /*
                           if (p < 2) {
                           System.out.println("Break due to packing constraint");
                           continue;
                           }
                           */
                        for (int u2 : adj[tmp[1]]) {
                            if (curr_solution[u2] < 0 && used.get(u2) && u2 != u) {
                                int c = 0;
                                for (int w : adj[u2]) {
                                    if (curr_solution[w] < 0) {
                                        if (ws[w] == u) {
                                            c++;
                                        } else if (w == u || !used.get(w)) {
                                            c = -1;
                                            break;
                                        }
                                    }
                                }
                                if (c == p - 1) {
                                    tmp[0] = 2;
                                    break;
                                }
                            }
                        }
                        // Add packing constraint for 'w'
                        packing.add(copyOf(tmp, p));
                    }
                }
            }
        }

        // Set branching vertex as not in cover
        set(v, 0);
        if (DEBUG >= 2 && depth <= maxDepth) {
            debug("branch (%d): 0%n", v_degree);
        }
        depth++;
        if (DEBUG >= 1) {
            debug("Performing rec on right child\n");
            //debug("Depth: %d\n", depth);
        }
        // nBranchings++; // see rec()
        // Process right child
        if ( TRACE > 0 && TRACE < 3) {
            System.out.format(" ^^ right_branch:       * %d\n", vertexID[v]);
        }
        rec("= 0");
        if ( TRACE > 0 && TRACE < 3) {
            System.out.format(" _ right_branch_done:   * %d\n", vertexID[v]);
        }
        while (packing.size() > oldP) {
            packing.remove(packing.size() - 1);
        }
        lb = oldLB;
        lbType = oldLBType;
        depth--;
        restore(pn);
        if (DEBUG >= 2) {
            debug("%-20s (%d): %s, %s\n", "Restoring", depth, getOptimalSolution(), getCurrentSolution());
        }
    } // end, branching()

    int lpLowerBound() {
        try (Stat stat = new Stat("lb_LP")) {
            return current_value + (remaining_vertices + 1) / 2;
        }
    }

    int cycleLowerBound() {
        try (Stat stat = new Stat("lb_cycle")) {
            long start_time = System.nanoTime();
            int lb = current_value;
            int[] id = iter;
            for (int i = 0; i < n; i++) id[i] = -1;
            int[] pos = que;
            int[] S = level, S2 = modTmp;
            // id[v] = the cycle v belongs to

            // for each vertex v, grab the largest possible cycle using only edges from the maximum matching, then check if it can be split
            for (int i = 0; i < n; i++) if (curr_solution[i] < 0 && id[i] < 0) {
                int v = i;
                int size = 0;
                // try to form a cycle S by only accepting an edge uv if l_u r_v was in the matching
                do {
                    Debug.check(id[v] < 0);
                    id[v] = i;
                    v = out_flow[v];
                    pos[v] = size;
                    S[size++] = v;
                } while (v != i);
                boolean clique = true;
                for (int j = 0; j < size; j++) {
                    v = S[j];
                    int num = 0;
                    for (int u : adj[v]) if (curr_solution[u] < 0 && id[u] == id[v]) num++;
                    if (num != size - 1) {
                        clique = false;
                        break;
                    }
                }
                if (clique) { // v is a part of a clique and all of its neighbors are in the same cycle
                    lb += size - 1;
                } else {
                    while (size >= 6) { // recursively split even cycles that have 6 or more vertices
                        int minSize = size, s = 0, t = size;
                        // look for pairs of indices, j, k such that v_j v_k+1 and v_j+1 v_k are edges
                        for (int j = 0; j < size; j++) {
                            used.clear();
                            v = S[j];
                            // Mark all of v_j neighbors as possible v_k+1 candidates
                            for (int u : adj[v]) if (curr_solution[u] < 0 && id[u] == id[v]) {
                                used.add(u);
                            }
                            v = S[(j + 1) % size];
                            // check if v_j+1 is adjacent to v_k
                            for (int u : adj[v]) if (curr_solution[u] < 0 && id[u] == id[v]) {
                                if (used.get(S[(pos[u] + 1) % size])) {
                                    int size2 = (pos[u] - j + size) % size;
                                    if (minSize > size2 && size2 % 2 != 0) { // split if cycle is even length
                                        minSize = size2;
                                        s = (j + 1) % size;
                                        t = (pos[u] + 1) % size;
                                    }
                                }
                            }
                        }
                        if (minSize == size) break; // no splitting of the cycle
                        int p = 0;
                        for (int j = t; j != s; j = (j + 1) % size) {
                            S2[p++] = S[j];
                        }
                        for (int j = s; j != t; j = (j + 1) % size) {
                            id[S[j]] = n;
                        }
                        int[] S3 = S; S = S2; S2 = S3;
                        size -= minSize;
                        // repeat using the larger cycle
                        Debug.check(size == p);
                        Debug.check(minSize > 1);
                        lb += (minSize + 1) / 2;
                        for (int j = 0; j < size; j++) pos[S[j]] = j;
                    }
                    Debug.check(size > 1);
                    lb += (size + 1) / 2;
                }
            }
            long end_time = System.nanoTime();
            cycleTime += end_time - start_time;
            return lb;
        } // try block (no catch)
    } // cycleLowerBound

    int cliqueLowerBound() {
        try (Stat stat = new Stat("lb_clique")) {
            long start_time = System.nanoTime();
            long[] ls = new long[remaining_vertices];
            int k = 0;
            int max_size = 0;
            int clique_count = 0;
            for (int i = 0; i < n; i++) {
                if (curr_solution[i] < 0) {
                    ls[k++] = ((long)deg(i)) << 32 | i;
                }
            }
            sort(ls);
            // ls[v] = deg(v) ~~~ v, i.e., upper half bits store degree,
            //  lower half store vertex id
            // ls is sorted in ascending order
            int[] clique = que, size = level, tmp = iter;
            int need = current_value;
            used.clear();
            // used = vertices that have been assigned a clique
            for (int i = 0; i < remaining_vertices; i++) {
                // clique[v] = the clique that v belongs to
                // size[v] = the size of v's clique
                // tmp[v] = the size of a potential clique 
                int v = (int)ls[i];
                int to = v, max = 0; // initially each vertex will default to
                                     // being its own clique
                for (int u : adj[v]) {
                    if (curr_solution[u] < 0 && used.get(u)) {
                        tmp[clique[u]] = 0;
                    }
                }
                // determines which clique to add v to:
                //      - count the number of neighbors that are in the same clique
                //      - if the count equals the size of the clique then we have a match!
                //      - e.g. u,v form a 2-clique (clique 1),
                //             x,y,a form a 3-clique (clique 2).
                //             w has neighbors u,v,x,y,z.
                //             the counts for w are : clique 1 = 2, clique 2 = 2
                //        since the count for clique 1 matches the size, add w to clique 1
                for (int u : adj[v]) {
                    if (curr_solution[u] < 0 && used.get(u)) {
                        int c = clique[u];
                        tmp[c]++;
                        if (tmp[c] == size[c] && max < size[c]) { 
                            to = c;
                            max = size[c];
                        }
                    }
                }
                clique[v] = to;
                if (to != v) {
                    size[to]++;
                    if (size[to] > max_size) {
                        max_size = size[to];
                    }
                    need++;
                } else {
                    // there are not cliques that v can be added to
                    size[v] = 1;
                    if (size[v] > max_size) {
                        max_size = size[v];
                    }
                    clique_count += 1;
                }
                used.add(v);
            }
            this.CLIQUE_STAT_MAX_CLIQUE_SIZE = max_size;
            this.CLIQUE_STAT_CLIQUE_COUNT = clique_count;
            long end_time = System.nanoTime();
            cliqueTime += end_time - start_time;
            return need;
        } // try block (no catch)
    } // cliqueLowerBound

    boolean decompose() {
        if ( DEBUG > 0 ) {
            debug("-> decompose, n = %4d, remaining_vertices = %4d%n",
                    n, remaining_vertices);
        }
        int[][] vss;
        try (Stat stat = new Stat("decompose")) {
            // there appears to be a repurposing of existing arrays level and
            // iter here
            int[] id = level;
            int[] size = iter;
            int number_of_components = 0;
            {
                // Compute connected components using BFS
                for (int i = 0; i < n; i++) {
                    id[i] = -1;
                }
                for (int s = 0; s < n; s++) {
                    if (curr_solution[s] < 0 && id[s] < 0) {
                        number_of_components++;
                        int qs = 0, qt = 0;
                        que[qt++] = s;
                        id[s] = s;
                        while (qs < qt) {
                            int v = que[qs++];
                            for (int u : adj[v]) {
                                if (curr_solution[u] < 0 && id[u] < 0) {
                                    id[u] = s;
                                    que[qt++] = u;
                                }
                            }
                        }
                        size[s] = qt;
                    }
                }
            }
            // at this point, id[v] is the id of the component to which v
            // belongs and size[c] is the number of vertices in component c;
            // a component c is numbered by the first vertex in it, so, e.g.,
            // a graph with components {1,2,5} and {3,4} would have
            // id[1] = id[2] = id[5] = 1 and id[3] = id[4] = 3
            // size[1] = 3 and size[3] = 2, but size[2], size[4] and size[5]
            // are undefined

            if (number_of_components <= 1
                    // this second condition is an efficiency hack:
                    // it causes a new, smaller instance of VCSolver to be
                    // created whenever: (a) the number of remaining vertices is
                    // only a fraction (SHRINK) of the original for this
                    // instance; and (b) the original number of vertices was
                    // large enough for this to matter.
                    && (n <= 100 || n * SHRINK < remaining_vertices)
               ) {
                if ( DEBUG > 0 ) {
                    debug("<- decompose (died), number of components = %d%n",
                            number_of_components);
                }
                return false;
               }

            long[] cs = new long[number_of_components];
            {
                int p = 0;
                for (int i = 0; i < n; i++) {
                    if (curr_solution[i] < 0 && id[i] == i) {
                        cs[p++] = ((long)(size[i])) << 32 | i;
                    }
                }
                sort(cs);
            }
            vss = new int[number_of_components][];
            int[] qs = new int[n];
            {
                for (int i = 0; i < number_of_components; i++) {
                    vss[i] = new int[size[(int)cs[i]]];
                    qs[(int)cs[i]] = i;
                }
                int[] ps = new int[number_of_components];
                for (int i = 0; i < n; i++) {
                    if (curr_solution[i] < 0) {
                        int j = qs[id[i]];
                        vss[j][ps[j]++] = i;
                    }
                }
            }
            for (int i = 0; i < n; i++) {
                id[i] = -1;
            }
            for (int i = 0; i < vss.length; i++) {
                int[] vs = vss[i];
                long[] ls = new long[vs.length];
                for (int j = 0; j < vs.length; j++) {
                    ls[j] = ((long)(n - deg(vs[j]))) << 32 | vs[j];
                }
                sort(ls);
                for (int j = 0; j < vs.length; j++) {
                    vs[j] = (int)ls[j];
                }
            }
        }

        int[] curr_solution2 = curr_solution.clone();
        for (int i = modifiedN - 1; i >= 0; i--) {
            modifieds[i].reverse(curr_solution2);
        }
        int[] size = new int[vss.length];
        for (int i = 0; i < vss.length; i++) {
            size[i] = vss[i].length;
        }
        int[] pos1 = new int[N];
        int[] pos2 = new int[N];
        ArrayList<int[]> packingB = new ArrayList<int[]>();
        {
            fill(pos1, -1);
            for (int i = 0; i < vss.length; i++) {
                for (int j = 0; j < vss[i].length; j++) {
                    pos1[vss[i][j]] = i;
                    pos2[vss[i][j]] = j;
                }
            }
            boolean[] need = new boolean[N];
            for (int i = 0; i < packing.size(); i++) {
                int[] ps = packing.get(i);
                int max = ps.length - 1 - ps[0], sum = 0, count = 0;
                for (int j = 1; j < ps.length; j++) {
                    int v = ps[j];
                    if (curr_solution2[v] < 0 || curr_solution2[v] == 2) {
                        count++;
                    }
                    if (curr_solution2[v] == 1) {
                        sum++;
                    }
                }
                if (sum > max) {
                    if ( DEBUG > 0 ) {
                        debug("<- decompose (true) sum = %4d, max = %4d%n", sum, max);
                    }
                    return true;
                }
                if (sum + count > max) {
                    packingB.add(ps);
                    for (int k = 1; k < ps.length; k++) {
                        if (curr_solution2[ps[k]] == 2) {
                            need[ps[k]] = true;
                        }
                    }
                }
            }
            for (int i = 0; i < modifiedN; i++) {
                boolean b = false;
                Modified mod = modifieds[i];
                for (int v : mod.removed) {
                    if (need[v]) {
                        b = true;
                    }
                }
                if (b) {
                    if (mod instanceof Fold) {
                        if (curr_solution2[mod.vs[0]] == 2) {
                            need[mod.vs[0]] = true;
                        }
                    } else {
                        for (int v : mod.vs) {
                            if (curr_solution2[v] == 2) {
                                need[v] = true;
                            }
                        }
                    }
                }
            }
            for (int i = modifiedN - 1; i >= 0; i--) {
                Modified mod = modifieds[i];
                boolean b = false;
                for (int v : mod.removed) {
                    if (need[v]) b = true;
                }
                if (b) {
                    if (mod instanceof Fold) {
                        for (int v : mod.removed) {
                            Debug.check(pos1[v] == -1);
                            pos1[v] = pos1[mod.vs[0]];
                            Debug.check(pos1[v] >= 0);
                            pos2[v] = size[pos1[v]]++;
                        }
                    } else {
                        int max = -1;
                        for (int v : mod.vs) {
                            if (max < pos1[v]) max = pos1[v];
                        }
                        Debug.check(max >= 0);
                        for (int v : mod.removed) {
                            Debug.check(pos1[v] == -1);
                            pos1[v] = max;
                            pos2[v] = size[pos1[v]]++;
                        }
                    }
                }
            }
            for (int i = 0; i < n; i++) {
                if ((curr_solution2[i] == 0 || curr_solution2[i] == 1) && pos1[i] >= 0) {
                    Debug.print(i, n, curr_solution[i]);
                    Debug.check(false);
                }
            }
        }

        // create smaller solvers for each component and initialize flow for each component
        VCSolver[] vcs = new VCSolver[vss.length];
        {
            for (int i = 0; i < vss.length; i++) {
                int[] vs = vss[i];
                size[i] += 2;
                int[][] adj2 = new int[vs.length][];
                for (int j = 0; j < vs.length; j++) {
                    adj2[j] = new int[deg(vs[j])];
                    int p = 0;
                    for (int u : adj[vs[j]]) {
                        if (curr_solution[u] < 0) {
                            adj2[j][p++] = pos2[u];
                        }
                    }
                    Debug.check(p == adj2[j].length);
                    sort(adj2[j]);
                }
                vcs[i] = new VCSolver(adj2, size[i]);
                for (int j = 0; j < vs.length; j++) {
                    if (in_flow[vs[j]] >= 0 && pos1[in_flow[vs[j]]] == i && pos2[in_flow[vs[j]]] < vs.length) {
                        vcs[i].in_flow[j] = pos2[in_flow[vs[j]]];
                    }
                    if (out_flow[vs[j]] >= 0 && pos1[out_flow[vs[j]]] == i && pos2[out_flow[vs[j]]] < vs.length) {
                        vcs[i].out_flow[j] = pos2[out_flow[vs[j]]];
                    }
                }
                vcs[i].curr_solution[vcs[i].N - 2] = vcs[i].optimal_solution[vcs[i].N - 2] = 0;
                vcs[i].curr_solution[vcs[i].N - 1] = vcs[i].optimal_solution[vcs[i].N - 1] = 1;
            }
        }

        // Create/modify packing constraints for each component
        {
            for (int i = 0; i < packingB.size(); i++) {
                int[] ps = packingB.get(i);
                int maxID = -1;
                for (int j = 1; j < ps.length; j++) {
                    int v = ps[j];
                    if (curr_solution2[v] < 0 || curr_solution2[v] == 2) {
                        maxID = Math.max(maxID, pos1[v]);
                    }
                }
                vcs[maxID].packing.add(ps);
            }
        }

        // Update modified graphs for each components
        {
            for (int i = 0; i < modifiedN; i++) {
                Modified mod = modifieds[i];
                int p = pos1[mod.removed[0]];
                if (p >= 0) {
                    vcs[p].modifieds[vcs[p].modifiedN++] = mod;
                }
            }
        }

        int[][] vss2 = new int[vss.length][];
        {
            for (int i = 0; i < vss.length; i++) {
                vss2[i] = new int[vcs[i].N - 2];
            }
            for (int i = 0; i < N; i++) {
                if (pos1[i] >= 0) {
                    vss2[pos1[i]][pos2[i]] = i;
                }
            }
        }

        // Process each component
        int sum = current_value;
        for (int i = 0; i < vss.length && optimal_value > sum; i++) {
            VCSolver vc = vcs[i];

            // packing 
            {
                ArrayList<int[]> packing2 = new ArrayList<int[]>();
                for (int j = 0; j < vc.packing.size(); j++) {
                    int[] ps = vc.packing.get(j);
                    int[] tmp = level;
                    int p = 0;
                    tmp[p++] = ps[0];
                    for (int k = 1; k < ps.length; k++) {
                        int v = ps[k];
                        if (pos1[v] == i) {
                            tmp[p++] = pos2[v];
                        } else {
                            Debug.check(curr_solution2[v] == 0 || curr_solution2[v] == 1);
                            if (curr_solution2[v] == 0) {
                                tmp[0]--;
                            }
                        }
                    }
                    if (p - 1 < tmp[0]) {
                        if ( DEBUG > 0 ) {
                            debug("<- decompose (true), p = %4d, tmp[0] = %4d%n",
                                    p, tmp[0]);
                        }
                        return true;
                    }
                    if (tmp[0] <= 0) {
                        continue;
                    }
                    packing2.add(copyOf(tmp, p));
                }
                vc.packing = packing2;
            } // packing

            // modified graphs (fold2, twin, funnel, desk)
            {
                for (int j = 0; j < vc.modifiedN; j++) {
                    Modified mod = vc.modifieds[j];
                    int[] removed = new int[mod.removed.length];
                    for (int k = 0; k < removed.length; k++) {
                        int v = mod.removed[k];
                        Debug.check(pos1[v] == i);
                        removed[k] = pos2[v];
                    }
                    if (mod instanceof Fold) {
                        int[] vs = new int[1];
                        int v = mod.vs[0];
                        if (pos1[v] == i) {
                            vs[0] = pos2[v];
                        } else {
                            Debug.check(curr_solution2[v] == 0 || curr_solution2[v] == 1);
                            vs[0] = vc.N - 2 + curr_solution2[v];
                        }
                        mod = new Fold(removed, vs);
                    } else {
                        int[] vs = new int[mod.vs.length];
                        for (int k = 0; k < vs.length; k++) {
                            int v = mod.vs[k];
                            if (pos1[v] == i) {
                                vs[k] = pos2[v];
                            } else {
                                Debug.check(curr_solution2[v] == 0 || curr_solution2[v] == 1);
                                vs[k] = vc.N - 2 + curr_solution2[v];
                            }
                        }
                        mod = new Alternative(removed, vs, ((Alternative)mod).k);
                    }
                    vc.modifieds[j] = mod;
                }
            } // modified graph

            vc.depth = depth + (vss.length > 1 ? 1 : 0);

            if (DEBUG >= 2 && depth <= maxDepth) {
                if (vss.length == 1) {
                    debug("shrink: %d -> %d (%d)%n", n, vcs[i].n, vcs[i].N);
                } else {
                    debug("decompose: %d (%d)%n", vcs[i].n, vcs[i].N);
                }
            }

            if (i + 1 == vss.length) {
                vc.optimal_value = Math.min(vss[i].length, optimal_value - sum);
            }

            vc.reverse();

            for (int j = 0; j < vc.N; j++) {
                Debug.check(vc.optimal_solution[j] == 0 || vc.optimal_solution[j] == 1);
            }

            if (DEBUG >= 2) {
                debug("In decompose:\n");
            }

            // Component solve
            vc.isComponentSolve();
            vc.solve();

            if (DEBUG >= 2) {
                debug("Out of decompose:\n");
            }
            sum += vc.optimal_value;
            for (int j = 0; j < vc.N - 2; j++) {
                curr_solution2[vss2[i][j]] = vc.optimal_solution[j];
                Debug.check(vc.optimal_solution[j] == 0 || vc.optimal_solution[j] == 1);
            }
        } // for each component i

        if (optimal_value > sum) {
            if (DEBUG >= 2 && rootDepth <= maxDepth) {
                debug("decomp optimal_value: %d -> %d%n", optimal_value, sum);
            }
            optimal_value = sum;
            System.arraycopy(curr_solution, 0, optimal_solution, 0, N);
            for (int i = 0; i < vss.length; i++) {
                for (int j = 0; j < vss[i].length; j++) {
                    optimal_solution[vss[i][j]] = vcs[i].optimal_solution[j];
                }
            }
            reverse();
        }
        if ( DEBUG > 0 ) {
            debug("<- decompose (true), done%n");
        }
        return true;
    }

    int lowerBound() {
        int tmp;
        if (DEBUG >= 2) {
            debug("%-20s (%d): %s, %s\n", "before lower bound", depth, getOptimalSolution(), getCurrentSolution());
        }
        if (lb < current_value) {
            lb = current_value;
            this.lbType = LowerBoundType.TRIVIAL;
        }
        if (CLIQUE_LOWER_BOUND) {
            tmp = cliqueLowerBound();
            if (lb < tmp) {
                lb = tmp;
                this.lbType = LowerBoundType.CLIQUE;
            }
        }
        if (LP_LOWER_BOUND) {
            tmp = lpLowerBound();
            if (lb < tmp) {
                lb = tmp;
                this.lbType = LowerBoundType.LP;
            }
        }
        if (CYCLE_LOWER_BOUND) {
            tmp = cycleLowerBound();
            if (lb < tmp) {
                lb = tmp;
                this.lbType = LowerBoundType.CYCLE;
            }
        }
        if (DEBUG >= 2 && depth <= maxDepth) {
          debug("lb = %d, opt_value = %d, type = %s%n", lb, optimal_value,
                getLBTypeString(this.lbType));
        }
        if ( depth == 0 ) {
            this.lbAtRoot = lb;
        }
        if (DEBUG >= 2) {
            debug("%-20s (%d): %s, %s\n", "after lower bound", depth, getOptimalSolution(), getCurrentSolution());
        }
        return lb;
    }

    // Return true if "quit reductions" or packing reduction returns -1
    boolean reduce() {
        int oldn = remaining_vertices;
        if (DEBUG >= 2) {
            debug("%-20s (%d): %s, %s\n", "before reductions", depth, getOptimalSolution(), getCurrentSolution());
        }
        for (;;) {
            if (density >= MIN_DENSITY_THRESHOLD && density <= MAX_DENSITY_THRESHOLD) {
                if (DEGREE1_REDUCTION) {
                    if (DV_DD_THRESHOLD == 0.00 || getDV() >= DV_DD_THRESHOLD) {
                        reduce_counts[REDUCE_TYPES.DEG_ONE.ordinal()]++;
                        if (deg1Reduction()) {
                            reduce_effective_counts[REDUCE_TYPES.DEG_ONE.ordinal()]++;
                        }
                    }
                }

                // Decompose into components, i.e., stop doing reductions, here if:
                //  - there were more than 100 vertices to begin with
                //  - reductions have reduced the number of vertices
                //    sufficiently, i.e., by at least a factor of SHRINK
                //  - [the role of outputLP is not clear; it's false by default]
                // Note: the main decompose takes place later in the code
                if (n > 100 && n * SHRINK >= remaining_vertices && !outputLP && decompose()) {
                    if (DEBUG >= 2) {
                        debug("Give up on reductions and do something else\n");
                    }
                    return true;
                }
            }
            if (!DENSITY_REDUCTIONS || density <= DENSITY_SKIP_THRESHOLD) {
                if (FOLD2_REDUCTION) {
                    reduce_counts[REDUCE_TYPES.FOLD_TWO.ordinal()]++;
                    if(fold2Reduction()) {
                        reduce_effective_counts[REDUCE_TYPES.FOLD_TWO.ordinal()]++;
                        continue;
                    }
                }
                if (TWIN_REDUCTION) {
                    reduce_counts[REDUCE_TYPES.TWIN.ordinal()]++;
                    if (twinReduction()) {
                        reduce_effective_counts[REDUCE_TYPES.TWIN.ordinal()]++;
                        continue;
                    }
                }
                if (DESK_REDUCTION) {
                    reduce_counts[REDUCE_TYPES.DESK.ordinal()]++;
                    if (deskReduction()) {
                        reduce_effective_counts[REDUCE_TYPES.DESK.ordinal()]++;
                        continue;
                    }
                }
            }
            if (density >= MIN_DENSITY_THRESHOLD && density <= MAX_DENSITY_THRESHOLD) {
                if (DOMINANCE_REDUCTION) {
                    if (DV_DD_THRESHOLD == 0.00 || getDV() >= DV_DD_THRESHOLD) {
                        reduce_counts[REDUCE_TYPES.DOMINANCE.ordinal()]++; 
                        if (dominateReduction()) {
                            reduce_effective_counts[REDUCE_TYPES.DOMINANCE.ordinal()]++;
                            continue;
                        }
                    }
                }
            }
            if (!DENSITY_REDUCTIONS || density <= DENSITY_SKIP_THRESHOLD) {
                if (UNCONFINED_REDUCTION) {
                    reduce_counts[REDUCE_TYPES.UNCONFINED.ordinal()]++; 
                    if (unconfinedReduction()) {
                        reduce_effective_counts[REDUCE_TYPES.UNCONFINED.ordinal()]++;
                        continue;
                    }
                }
            }
            if (!DENSITY_REDUCTIONS || density > DENSITY_SKIP_THRESHOLD || !INITIAL_REDUCTION) {
                if (LP_REDUCTION) {
                    if (OC_LP_THRESHOLD == 1.00 || getOC() > OC_LP_THRESHOLD) {
                        reduce_counts[REDUCE_TYPES.LP.ordinal()]++;
                        if (lpReduction()) {
                            reduce_effective_counts[REDUCE_TYPES.LP.ordinal()]++;
                            continue;
                        }
                    }
                }
            }
            if (PACKING_REDUCTION) {
                int r = packingReduction();
                reduce_counts[REDUCE_TYPES.PACKING.ordinal()]++;
                if (r < 0) {
                    return true;
                }
                if (r > 0) {
                    reduce_effective_counts[REDUCE_TYPES.PACKING.ordinal()]++;
                    continue;
                }
            }
            if (!DENSITY_REDUCTIONS || density <= DENSITY_SKIP_THRESHOLD) {
                if (FUNNEL_REDUCTION) {
                    reduce_counts[REDUCE_TYPES.FUNNEL.ordinal()]++;
                    if (funnelReduction()) {
                        reduce_effective_counts[REDUCE_TYPES.FUNNEL.ordinal()]++;
                        continue;
                    }
                }
            }
            break;
        }
        if (DEBUG >= 2 && depth <= maxDepth && oldn != remaining_vertices) {
            debug("reduce: %d -> %d%n", oldn, remaining_vertices);
        }
        if (DEBUG >= 2) {
            debug("%-20s (%d): %s, %s\n", "after reductions", depth, getOptimalSolution(), getCurrentSolution());
        }
        return false;
    }

    /**
     * Process a "node"
     */
    void rec(String label) {
        // check for timeout
        double current = 1e-9 * System.nanoTime();
        if ( current >= timelimit ) return;
        if ( current >= previous + PRINT_INTERVAL
             && current > startTime + PRINT_INTERVAL
             && ! QUIET ) {
            System.err.format("%6.1f seconds\n", current - startTime);
            previous = current;
        }

        if (!PACKING_REDUCTION) {
            Debug.check(packing.size() == 0);
        }

        if (remaining_vertices <= TARGET_SIZE) {
            if (reduce()) {
                printNode(label, NODE_RED_CUT_STRING);
                return;
            }
        }
        if ( lowerBound() >= optimal_value ) {
            incrementLBCount(this.lbType);
            printNode(label, NODE_LB_CUT_STRING + ", "
                      + getLBTypeString(this.lbType));
            printLBInfo(this.lbType);
            return;
        }
        if (remaining_vertices == 0) {
            if (DEBUG >= 2 && rootDepth <= maxDepth) {
                debug("rec optimal_value: %d -> %d%n", optimal_value, current_value);
                debug("%-20s (%d): %s, %s\n", "", depth, getOptimalSolution(), getCurrentSolution());
            }
            optimal_value = current_value;
            System.arraycopy(curr_solution, 0, optimal_solution, 0, N);
            reverse();
            if (DEBUG >= 2 && rootDepth <= maxDepth) {
                debug("rec optimal_value: %d -> %d%n", optimal_value, current_value);
                debug("%-20s (%d): %s, %s\n", "", depth, getOptimalSolution(), getCurrentSolution());
            }
            printNode(label, NODE_SOLVED_STRING);
            return;
        }
        if (!INITIAL_REDUCTION) {
            INITIAL_REDUCTION = true;
            if (DISABLE_REDUCTIONS) {
                for (int i = 0; i < reduce_counts.length; i++) {
                    // If the effective ratio is < 0.5, don't do the reduction later
                    if ((1.0 * reduce_effective_counts[i] / reduce_counts[i]) < DISABLE_EFFICIENCY_THRESHOLD) {
                        switch (i) { 
                            case 0: 
                                    if (!TIERED_DISABLE) {
                                        DEGREE1_REDUCTION = false;
                                        System.out.println("Skipping Deg1");
                                    }
                                    break;
                            case 1: 
                                    if (!TIERED_DISABLE) {
                                        DOMINANCE_REDUCTION = false;
                                        System.out.println("Skipping Dom");
                                    }
                                    break;
                            case 2: 
                                    if (!TIERED_DISABLE) {
                                        UNCONFINED_REDUCTION = false;
                                        System.out.println("Skipping Unconfined");
                                    }
                                    break;
                            case 3: 
                                    if (!(LP_LOWER_BOUND || CYCLE_LOWER_BOUND)) {
                                        LP_REDUCTION = false;
                                        System.out.println("Skipping LP");
                                    }
                                    break;
                            case 4: PACKING_REDUCTION = false;
                                    System.out.println("Skipping Packing");
                                    break;
                            case 5: FOLD2_REDUCTION = false;
                                    System.out.println("Skipping Fold2");
                                    break;
                            case 6: TWIN_REDUCTION = false;
                                    System.out.println("Skipping Twin");
                                    break;
                            case 7: FUNNEL_REDUCTION = false;
                                    System.out.println("Skipping Funnel");
                                    break;
                            case 8: DESK_REDUCTION = false;
                                    System.out.println("Skipping Desk");
                                    break;
                        }
                    }
                }
                DISABLE_REDUCTIONS = false;
            }
        }
        if (DEBUG >= 2) {
            debug("%-20s (%d): %s, %s\n", "before decompose", depth, getOptimalSolution(), getCurrentSolution());
        }
        printNode(label, NODE_ALIVE_STRING);
        if (decompose()) {
            return;
        }
        if (DEBUG >= 2) {
            debug("%-20s (%d): %s, %s\n", "after decompose", depth, getOptimalSolution(), getCurrentSolution());
        }

        if (!ONLY_ROOT) {
            branching();
        }
    }

    void debug(String str, Object...os) {
        StringBuilder sb = new StringBuilder();
        Calendar c = Calendar.getInstance();
        sb.append(String.format("%02d:%02d:%02d  ", c.get(Calendar.HOUR_OF_DAY), c.get(Calendar.MINUTE), c.get(Calendar.SECOND)));
        for (int i = 0; i < depth && i <= maxDepth; i++) {
            sb.append(' ');
        }
        System.err.print(sb);
        System.err.printf(str, os);
    }

    public int solve() {
        if (DEBUG >= 3) {
            System.out.print(getAdjList());
            System.out.println("<<<<<");
        }
        if (CYCLE_LOWER_BOUND && !LP_REDUCTION && !outputLP) {
            System.err.println("LP/cycle lower bounds require LP reduction.");
            Debug.check(false);
        }
        rootDepth = depth;
        if (outputLP) {
            if (DEGREE1_REDUCTION || DOMINANCE_REDUCTION || FOLD2_REDUCTION || LP_REDUCTION || UNCONFINED_REDUCTION || TWIN_REDUCTION || FUNNEL_REDUCTION || DESK_REDUCTION || PACKING_REDUCTION) {
                reduce();
            } else {
                lpReduction();
                reduce_counts[REDUCE_TYPES.LP.ordinal()]++;
            }
            System.out.printf("%.1f%n", current_value + remaining_vertices / 2.0);
            return optimal_value;
        }
        if (DEBUG >= 2) {
            debug("Performing rec on root\n");
        }

        rec("RT ");

        if (DEBUG >= 2 && depth <= maxDepth) {
            debug("optimal_value: %d%n", optimal_value);
        }
        if (DEBUG >= 2) {
            debug("optimal solution: %s\n", getOptimalSolution());
        }
        return optimal_value;
    }

}

//  [Last modified: 2020 02 05 at 19:27:49 GMT]
