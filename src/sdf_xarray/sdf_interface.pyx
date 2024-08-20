cimport csdf

import dataclasses
import time


cdef list[str] _sdf_type_mapping = [
    "",
    "i4",
    "i8",
    "f4",
    "f8",
    "f16",
    "s",
    "bool",
]


@dataclasses.dataclass
cdef class Block:
    _id: str
    name: str
    data_length: int
    dtype: str
    ndims: int

    # cdef public list dims
    # cdef public str units
    # cdef public int grid_id


    # cdef public PyObject data
    # cdef public PyObject extents
    # cdef public PyObject geometry
    # cdef public PyObject species_id
    # cdef public PyObject mult
    # cdef public int stagger
    # cdef public PyObject dict
    # cdef public PyObject material_names
    # cdef public PyObject material_ids

    # cdef public PyObject blocklist
    # cdef public Block grid
    # cdef public Block grid_mid
    # cdef public Block parent
    # cdef public SDFObject sdf
    # cdef public sdf_block_t b

    # cdef public int sdfref
    # cdef public int adims[4]

@dataclasses.dataclass
cdef class Constant:
    _id: str
    name: str
    dtype: str
    data: int | str | float


cdef class SDFFile:
    cdef csdf.sdf_file_t* _c_sdf_file
    cdef public str filename
    cdef public dict header, run_info
    cdef public dict[str, Block] variables

    def __cinit__(self, filename: str):
        self._c_sdf_file = csdf.sdf_open(
            filename.encode("UTF-8"), 0, csdf.SDF_READ, False
        )
        if self._c_sdf_file == NULL:
            raise IOError(f"Failed to open SDF file '{filename}'")

        csdf.sdf_stack_init(self._c_sdf_file)
        csdf.sdf_read_blocklist_all(self._c_sdf_file)

        self.header = {
            "filename": filename,
            "file_version": self._c_sdf_file.file_version,
            "file_revision": self._c_sdf_file.file_revision,
            "code_name": self._c_sdf_file.code_name.decode("UTF-8"),
            "step": self._c_sdf_file.step,
            "time": self._c_sdf_file.time,
            "jobid1": self._c_sdf_file.jobid1,
            "jobid2": self._c_sdf_file.jobid2,
            "code_io_version": self._c_sdf_file.code_io_version,
            "restart_flag": bool(self._c_sdf_file.restart_flag),
            "other_domains": bool(self._c_sdf_file.other_domains),
            "station_file": bool(self._c_sdf_file.station_file),
        }
        self._read_variable_metadata()

    cdef _read_variable_metadata(self):
        cdef csdf.sdf_block_t* block = self._c_sdf_file.blocklist
        cdef csdf.run_info* run = NULL

        self.variables = {}

        for i in range(self._c_sdf_file.nblocks):
            name = block.name.decode("UTF-8")

            if block.blocktype == csdf.SDF_BLOCKTYPE_RUN_INFO:
                run = <csdf.run_info*>block.data
                self.run_info = {
                    "version": f"{run.version}.{run.revision}.{run.minor_rev}",
                    "commit_id": run.commit_id.decode("UTF-8"),
                    "sha1sum": run.sha1sum.decode("UTF-8"),
                    "compile_machine": run.compile_machine.decode("UTF-8"),
                    "compile_flags": run.compile_flags.decode("UTF-8"),
                    "defines": f"{run.defines}",
                    "compile_date": time.ctime(run.compile_date),
                    "run_date": time.ctime(run.run_date),
                    "io_date": time.ctime(run.io_date),
                }
            else:
                self.variables[name] = Block(
                    _id=block.id.decode("UTF-8"),
                    name=name,
                    data_length=block.data_length,
                    dtype=_sdf_type_mapping[block.datatype_out],
                    ndims=block.ndims,
            )

            block = block.next
            
    def close(self):
        csdf.sdf_stack_destroy(self._c_sdf_file)
        csdf.sdf_close(self._c_sdf_file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
