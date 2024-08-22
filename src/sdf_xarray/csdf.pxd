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
        double mult, time, time_increment
        int64_t dims[SDF_MAXDIMS]
        int64_t local_dims[SDF_MAXDIMS]
        int64_t data_length
        int32_t ndims, geometry, datatype, blocktype
        int32_t stagger, datatype_out
        char const_value[16]
        char* id
        char* units
        char* mesh_id
        char* material_id
        char* name
        char* material_name
        char** dim_labels
        char** dim_units
        char** variable_ids
        void** grids
        void* data
        sdf_block_t* next

    ctypedef struct sdf_file_t:
        int32_t sdf_lib_version, sdf_lib_revision
        int32_t sdf_extension_version, sdf_extension_revision
        int32_t file_version, file_revision
        double time
        int64_t current_location
        int32_t jobid1, jobid2, endianness, summary_size
        int32_t block_header_length, string_length, id_length
        int32_t code_io_version, step
        int32_t nblocks
        char* buffer
        char* filename
        bint restart_flag, other_domains
        bint station_file
        bint restart_flag
        char* code_name
        sdf_block_t* blocklist
        sdf_block_t* current_block

    cdef struct run_info:
        int64_t defines
        int32_t version, revision, compile_date, run_date, io_date, minor_rev
        char* commit_id
        char* sha1sum
        char* compile_machine
        char* compile_flags

    sdf_file_t *sdf_open(const char *filename, comm_t comm, int mode, int use_mmap)
    bint sdf_close(sdf_file_t *h)
    sdf_block_t *sdf_find_block_by_name(sdf_file_t *h, const char *name)
    bint sdf_read_header(sdf_file_t *h)
    bint sdf_read_blocklist_all(sdf_file_t *h)
    bint sdf_read_block_info(sdf_file_t *h)
    bint sdf_read_data(sdf_file_t *h)
    bint sdf_get_domain_bounds(sdf_file_t *h, int rank,
                                 int *starts, int *local_dims)
    int sdf_block_set_array_section(sdf_block_t *b, const int ndims,
                                       const int64_t *starts, const int64_t *ends,
                                       const int64_t *strides)


cdef extern from "sdf_helper.h":
    bint sdf_helper_read_data(sdf_file_t *h, sdf_block_t *b)


cdef extern from "stack_allocator.h":
    void sdf_stack_destroy(sdf_file_t *h)
    void sdf_stack_init(sdf_file_t *h)
