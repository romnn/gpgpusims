
enum scheduler_prioritization_type
{
    SCHEDULER_PRIORITIZATION_LRR = 0, // Loose Round Robin
    SCHEDULER_PRIORITIZATION_SRR, // Strict Round Robin
    SCHEDULER_PRIORITIZATION_GTO, // Greedy Then Oldest
    SCHEDULER_PRIORITIZATION_GTLRR, // Greedy Then Loose Round Robin
    SCHEDULER_PRIORITIZATION_GTY, // Greedy Then Youngest
    SCHEDULER_PRIORITIZATION_OLDEST, // Oldest First
    SCHEDULER_PRIORITIZATION_YOUNGEST, // Youngest First
};


enum concrete_scheduler
{
    CONCRETE_SCHEDULER_LRR = 0,
    CONCRETE_SCHEDULER_GTO,
    CONCRETE_SCHEDULER_TWO_LEVEL_ACTIVE,
    CONCRETE_SCHEDULER_WARP_LIMITING,
    NUM_CONCRETE_SCHEDULERS
};


class scheduler_unit { //this can be copied freely, so can be used in std containers.
public:
    scheduler_unit(shader_core_stats* stats, shader_core_ctx* shader, 
                   Scoreboard* scoreboard, simt_stack** simt, 
                   std::vector<shd_warp_t>* warp, 
                   register_set* sp_out,
                   register_set* sfu_out,
                   register_set* mem_out,
                   int id) 
        : m_supervised_warps(), m_stats(stats), m_shader(shader),
        m_scoreboard(scoreboard), m_simt_stack(simt), /*m_pipeline_reg(pipe_regs),*/ m_warp(warp),
        m_sp_out(sp_out),m_sfu_out(sfu_out),m_mem_out(mem_out), m_id(id){}
    virtual ~scheduler_unit(){}
    virtual void add_supervised_warp_id(int i) {
        m_supervised_warps.push_back(&warp(i));
    }
    virtual void done_adding_supervised_warps() {
        m_last_supervised_issued = m_supervised_warps.end();
    }


    // The core scheduler cycle method is meant to be common between
    // all the derived schedulers.  The scheduler's behaviour can be
    // modified by changing the contents of the m_next_cycle_prioritized_warps list.
    void cycle();

    // These are some common ordering fucntions that the
    // higher order schedulers can take advantage of
    template < typename T >
    void order_lrr( typename std::vector< T >& result_list,
                    const typename std::vector< T >& input_list,
                    const typename std::vector< T >::const_iterator& last_issued_from_input,
                    unsigned num_warps_to_add );
    
    enum OrderingType 
    {
        // The item that issued last is prioritized first then the sorted result
        // of the priority_function
        ORDERING_GREEDY_THEN_PRIORITY_FUNC = 0,
        // No greedy scheduling based on last to issue. Only the priority function determines
        // priority
        ORDERED_PRIORITY_FUNC_ONLY,
        NUM_ORDERING,
    };
    template < typename U >
    void order_by_priority( std::vector< U >& result_list,
                            const typename std::vector< U >& input_list,
                            const typename std::vector< U >::const_iterator& last_issued_from_input,
                            unsigned num_warps_to_add,
                            OrderingType age_ordering,
                            bool (*priority_func)(U lhs, U rhs) );
    static bool sort_warps_by_oldest_dynamic_id(shd_warp_t* lhs, shd_warp_t* rhs);

    // Derived classes can override this function to populate
    // m_supervised_warps with their scheduling policies
    virtual void order_warps() = 0;

protected:
    virtual void do_on_warp_issued( unsigned warp_id,
                                    unsigned num_issued,
                                    const std::vector< shd_warp_t* >::const_iterator& prioritized_iter );
    inline int get_sid() const;
protected:
    shd_warp_t& warp(int i);

    // This is the prioritized warp list that is looped over each cycle to determine
    // which warp gets to issue.
    std::vector< shd_warp_t* > m_next_cycle_prioritized_warps;
    // The m_supervised_warps list is all the warps this scheduler is supposed to
    // arbitrate between.  This is useful in systems where there is more than
    // one warp scheduler. In a single scheduler system, this is simply all
    // the warps assigned to this core.
    std::vector< shd_warp_t* > m_supervised_warps;
    // This is the iterator pointer to the last supervised warp you issued
    std::vector< shd_warp_t* >::const_iterator m_last_supervised_issued;
    shader_core_stats *m_stats;
    shader_core_ctx* m_shader;
    // these things should become accessors: but would need a bigger rearchitect of how shader_core_ctx interacts with its parts.
    Scoreboard* m_scoreboard; 
    simt_stack** m_simt_stack;
    //warp_inst_t** m_pipeline_reg;
    std::vector<shd_warp_t>* m_warp;
    register_set* m_sp_out;
    register_set* m_sfu_out;
    register_set* m_mem_out;

    int m_id;
};