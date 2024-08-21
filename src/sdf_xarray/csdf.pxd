cdef extern from "<stdint.h>" nogil:
    ctypedef signed int int32_t
    ctypedef signed long int64_t

cdef extern from "sdf.h":
    cdef enum:
        SDF_VERSION
        SDF_REVISION
        SDF_LIB_VERSION
        SDF_LIB_REVISION
        SDF_MAGIC
        SDF_MAXDIMS
        SDF_READ
        SDF_BLOCKTYPE_SCRUBBED
        SDF_BLOCKTYPE_NULL
        SDF_BLOCKTYPE_PLAIN_MESH
        SDF_BLOCKTYPE_POINT_MESH
        SDF_BLOCKTYPE_PLAIN_VARIABLE
        SDF_BLOCKTYPE_POINT_VARIABLE
        SDF_BLOCKTYPE_CONSTANT
        SDF_BLOCKTYPE_ARRAY
        SDF_BLOCKTYPE_RUN_INFO
        SDF_BLOCKTYPE_SOURCE
        SDF_BLOCKTYPE_STITCHED_TENSOR
        SDF_BLOCKTYPE_STITCHED_MATERIAL
        SDF_BLOCKTYPE_STITCHED_MATVAR
        SDF_BLOCKTYPE_STITCHED_SPECIES
        SDF_BLOCKTYPE_SPECIES
        SDF_BLOCKTYPE_PLAIN_DERIVED
        SDF_BLOCKTYPE_POINT_DERIVED
        SDF_BLOCKTYPE_CONTIGUOUS_TENSOR
        SDF_BLOCKTYPE_CONTIGUOUS_MATERIAL
        SDF_BLOCKTYPE_CONTIGUOUS_MATVAR
        SDF_BLOCKTYPE_CONTIGUOUS_SPECIES
        SDF_BLOCKTYPE_CPU_SPLIT
        SDF_BLOCKTYPE_STITCHED_OBSTACLE_GROUP
        SDF_BLOCKTYPE_UNSTRUCTURED_MESH
        SDF_BLOCKTYPE_STITCHED
        SDF_BLOCKTYPE_CONTIGUOUS
        SDF_BLOCKTYPE_LAGRANGIAN_MESH
        SDF_BLOCKTYPE_STATION
        SDF_BLOCKTYPE_STATION_DERIVED
        SDF_BLOCKTYPE_DATABLOCK
        SDF_BLOCKTYPE_NAMEVALUE
        SDF_DATATYPE_NULL
        SDF_DATATYPE_INTEGER4
        SDF_DATATYPE_INTEGER8
        SDF_DATATYPE_REAL4
        SDF_DATATYPE_REAL8
        SDF_DATATYPE_REAL16
        SDF_DATATYPE_CHARACTER
        SDF_DATATYPE_LOGICAL
        SDF_DATATYPE_OTHER

    ctypedef int comm_t

    ctypedef struct sdf_block_t:
        double* extents
        double* dim_mults
        double* station_x
        double* station_y
        double* station_z
        double mult, time, time_increment
        int64_t dims[SDF_MAXDIMS]
        int64_t local_dims[SDF_MAXDIMS]
        int64_t block_start, next_block_location, data_location
        int64_t inline_block_start, inline_next_block_location
        int64_t summary_block_start, summary_next_block_location
        int64_t nelements, nelements_local, data_length
        int64_t* nelements_blocks
        int64_t* data_length_blocks
        int64_t* array_starts
        int64_t* array_ends
        int64_t* array_strides
        int64_t* global_array_starts
        int64_t* global_array_ends
        int64_t* global_array_strides
        int32_t ndims, geometry, datatype, blocktype, info_length
        int32_t type_size, stagger, datatype_out, type_size_out
        int32_t nstations, nvariables, step, step_increment
        int32_t* dims_in
        int32_t* station_nvars
        int32_t* variable_types
        int32_t* station_index
        int32_t* station_move
        int nm, n_ids, opt, ng, nfaces, ngrids, offset
        int ngb[6]
        char const_value[16]
        char* id
        char* units
        char* mesh_id
        char* material_id
        char* vfm_id
        char* obstacle_id
        char* station_id
        char* name
        char* material_name
        char* must_read
        char** dim_labels
        char** dim_units
        char** station_ids
        char** variable_ids
        char** station_names
        char** material_names
        int* node_list
        int* boundary_cells
        void** grids
        void* data
        char done_header, done_info, done_data, dont_allocate, dont_display
        char dont_own_data, use_mult, next_block_modified, rewrite_metadata
        char in_file, ng_any, no_internal_ghost
        sdf_block_t* next
        sdf_block_t* prev
        sdf_block_t* subblock
        sdf_block_t* subblock2

    ctypedef struct sdf_file_t:
        int64_t dbg_count
        int32_t sdf_lib_version, sdf_lib_revision
        int32_t sdf_extension_version, sdf_extension_revision
        int32_t file_version, file_revision
        char* dbg
        char* dbg_bu
        char** extension_names
        double time
        int64_t first_block_location, summary_location, start_location, soi, sof
        int64_t current_location
        int32_t jobid1, jobid2, endianness, summary_size
        int32_t block_header_length, string_length, id_length
        int32_t code_io_version, step
        int32_t nblocks, nblocks_file, error_code
        int rank, ncpus, ndomains, rank_master, indent, print
        char* buffer
        char* filename
        bint done_header, restart_flag, other_domains, use_float, use_summary
        bint use_random, station_file, swap
        bint inline_metadata_read, summary_metadata_read
        bint inline_metadata_invalid, summary_metadata_invalid, tmp_flag
        bint metadata_modified, can_truncate, first_block_modified
        char* code_name
        char* error_message
        sdf_block_t* blocklist
        sdf_block_t* tail
        sdf_block_t* current_block
        sdf_block_t* last_block_in_file
        char* mmap
        void* ext_data
        void* stack_handle
        int array_count, fd, purge_duplicated_ids
        int internal_ghost_cells
        int ignore_nblocks
        # FILE *filehandle
        # comm_t comm
        # sdf_block_t *hashed_blocks_by_id, *hashed_blocks_by_name

    cdef struct run_info:
        int64_t defines
        int32_t version, revision, compile_date, run_date, io_date, minor_rev
        char* commit_id
        char* sha1sum
        char* compile_machine
        char* compile_flags

    sdf_file_t *sdf_open(const char *filename, comm_t comm, int mode, int use_mmap)
    bint sdf_close(sdf_file_t *h)
    bint sdf_free_blocklist_data(sdf_file_t *h)
    sdf_block_t *sdf_find_block_by_name(sdf_file_t *h, const char *name)
    bint sdf_read_header(sdf_file_t *h)
    bint sdf_read_blocklist(sdf_file_t *h)
    bint sdf_read_blocklist_all(sdf_file_t *h)
    bint sdf_read_block_info(sdf_file_t *h)
    bint sdf_read_data(sdf_file_t *h)
    bint sdf_get_domain_bounds(sdf_file_t *h, int rank,
                                 int *starts, int *local_dims)
    int sdf_block_set_array_section(sdf_block_t *b, const int ndims,
                                       const int64_t *starts, const int64_t *ends,
                                       const int64_t *strides)
    char *sdf_get_library_commit_id()
    char *sdf_get_library_commit_date()
    bint sdf_has_debug_info()
    char *sdf_extension_get_info_string(sdf_file_t *h, const char *prefix)
    void sdf_extension_print_version(sdf_file_t *h)


cdef extern from "sdf_helper.h":
    bint sdf_helper_read_data(sdf_file_t *h, sdf_block_t *b)


cdef extern from "stack_allocator.h":
    void sdf_stack_alloc(sdf_file_t *h, sdf_block_t *b)
    void sdf_stack_free_block(sdf_file_t *h, sdf_block_t *b)
    void sdf_stack_push_to_bottom(sdf_file_t *h, sdf_block_t *b)
    void sdf_stack_freeup_memory(sdf_file_t *h)
    void sdf_stack_free(sdf_file_t *h)
    void sdf_stack_destroy(sdf_file_t *h)
    void sdf_stack_init(sdf_file_t *h)
