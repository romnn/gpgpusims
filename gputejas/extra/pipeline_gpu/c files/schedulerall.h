class lrr_scheduler : public scheduler_unit {
public:
	lrr_scheduler ( shader_core_stats* stats, shader_core_ctx* shader,
                    Scoreboard* scoreboard, simt_stack** simt,
                    std::vector<shd_warp_t>* warp,
                    register_set* sp_out,
                    register_set* sfu_out,
                    register_set* mem_out,
                    int id )
	: scheduler_unit ( stats, shader, scoreboard, simt, warp, sp_out, sfu_out, mem_out, id ){}
	virtual ~lrr_scheduler () {}
	virtual void order_warps ();
    virtual void done_adding_supervised_warps() {
        m_last_supervised_issued = m_supervised_warps.end();
    }
};

class gto_scheduler : public scheduler_unit {
public:
	gto_scheduler ( shader_core_stats* stats, shader_core_ctx* shader,
                    Scoreboard* scoreboard, simt_stack** simt,
                    std::vector<shd_warp_t>* warp,
                    register_set* sp_out,
                    register_set* sfu_out,
                    register_set* mem_out,
                    int id )
	: scheduler_unit ( stats, shader, scoreboard, simt, warp, sp_out, sfu_out, mem_out, id ){}
	virtual ~gto_scheduler () {}
	virtual void order_warps ();
    virtual void done_adding_supervised_warps() {
        m_last_supervised_issued = m_supervised_warps.begin();
    }

};


class two_level_active_scheduler : public scheduler_unit {
public:
	two_level_active_scheduler ( shader_core_stats* stats, shader_core_ctx* shader,
                          Scoreboard* scoreboard, simt_stack** simt,
                          std::vector<shd_warp_t>* warp,
                          register_set* sp_out,
                          register_set* sfu_out,
                          register_set* mem_out,
                          int id,
                          char* config_str )
	: scheduler_unit ( stats, shader, scoreboard, simt, warp, sp_out, sfu_out, mem_out, id ),
	  m_pending_warps() 
    {
        unsigned inner_level_readin;
        unsigned outer_level_readin; 
        int ret = sscanf( config_str,
                          "two_level_active:%d:%d:%d",
                          &m_max_active_warps,
                          &inner_level_readin,
                          &outer_level_readin);
        assert( 3 == ret );
        m_inner_level_prioritization=(scheduler_prioritization_type)inner_level_readin;
        m_outer_level_prioritization=(scheduler_prioritization_type)outer_level_readin;
    }
	virtual ~two_level_active_scheduler () {}
    virtual void order_warps();
	void add_supervised_warp_id(int i) {
        if ( m_next_cycle_prioritized_warps.size() < m_max_active_warps ) {
            m_next_cycle_prioritized_warps.push_back( &warp(i) );
        } else {
		    m_pending_warps.push_back(&warp(i));
        }
	}
    virtual void done_adding_supervised_warps() {
        m_last_supervised_issued = m_supervised_warps.begin();
    }

protected:
    virtual void do_on_warp_issued( unsigned warp_id,
                                    unsigned num_issued,
                                    const std::vector< shd_warp_t* >::const_iterator& prioritized_iter );

private:
	std::deque< shd_warp_t* > m_pending_warps;
    scheduler_prioritization_type m_inner_level_prioritization;
    scheduler_prioritization_type m_outer_level_prioritization;
	unsigned m_max_active_warps;
};

// Static Warp Limiting Scheduler
class swl_scheduler : public scheduler_unit {
public:
	swl_scheduler ( shader_core_stats* stats, shader_core_ctx* shader,
                    Scoreboard* scoreboard, simt_stack** simt,
                    std::vector<shd_warp_t>* warp,
                    register_set* sp_out,
                    register_set* sfu_out,
                    register_set* mem_out,
                    int id,
                    char* config_string );
	virtual ~swl_scheduler () {}
	virtual void order_warps ();
    virtual void done_adding_supervised_warps() {
        m_last_supervised_issued = m_supervised_warps.begin();
    }

protected:
    scheduler_prioritization_type m_prioritization;
    unsigned m_num_warps_to_limit;
};

