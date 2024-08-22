cimport csdf

import dataclasses
import time

from libc.string cimport memcpy
import numpy as np
cimport numpy as cnp
cnp.import_array()


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
    dims: tuple[int]


@dataclasses.dataclass
cdef class Variable(Block):
    units: tuple[str] | None
    mult: float | None
    grid: str | None
    grid_mid: str | None


cdef Variable make_Variable_from_sdf_block(str name, csdf.sdf_block_t* block):
    return Variable(
        _id=block.id.decode("UTF-8"),
        name=name,
        data_length=block.data_length,
        dtype=_sdf_type_mapping[block.datatype_out],
        ndims=block.ndims,
        dims=tuple(block.dims[i] for i in range(block.ndims)),
        units=block.units.decode("UTF-8") if block.units else None,
        mult=block.mult if block.mult else None,
        grid=block.mesh_id.decode("UTF-8") if block.mesh_id else None,
        grid_mid=f"{block.mesh_id.decode('UTF-8')}_mid" if block.mesh_id else None,
    )


@dataclasses.dataclass
cdef class Mesh(Block):
    units: tuple[str]
    labels: tuple[str]
    mults: tuple[float] | None
    parent: Mesh | None = None


cdef Mesh make_Mesh_from_sdf_block(str name, csdf.sdf_block_t* block):
    return Mesh(
        _id=block.id.decode("UTF-8"),
        name=name,
        data_length=block.data_length,
        dtype=_sdf_type_mapping[block.datatype_out],
        ndims=block.ndims,
        dims=tuple(block.dims[i] for i in range(block.ndims)),
        units=tuple(block.dim_units[i].decode("UTF-8") for i in range(block.ndims)),
        labels=tuple(block.dim_labels[i].decode("UTF-8") for i in range(block.ndims)),
        mults=(
            tuple(block.dim_mults[i] for i in range(block.ndims))
            if block.dim_mults
            else None
        ),
    )

@dataclasses.dataclass
cdef class Constant:
    _id: str
    name: str
    data: int | str | float


cdef Constant make_Constant(str name, csdf.sdf_block_t* block):
    data: int | str | float | double

    if block.datatype == csdf.SDF_DATATYPE_REAL4:
        data = (<float*>block.const_value)[0]
    elif block.datatype == csdf.SDF_DATATYPE_REAL8:
        data = (<double*>block.const_value)[0]
    if block.datatype == csdf.SDF_DATATYPE_INTEGER4:
        data = (<csdf.int32_t*>block.const_value)[0]
    if block.datatype == csdf.SDF_DATATYPE_INTEGER8:
        data = (<csdf.int64_t*>block.const_value)[0]

    return Constant(
        _id=block.id.decode("UTF-8"), name=name, data=data
    )


cdef class SDFFile:
    """Read an SDF file

    Attributes
    ----------
    header: dict
        File metadata
    run_info: dict
        More metadata
    variables: dict[str, Variable]
        Mapping of variable name to metadata
    grids: dict[str, Mesh]
        Mapping of grid ID to metadata

    """
    cdef csdf.sdf_file_t* _c_sdf_file
    cdef public str filename
    cdef public dict header, run_info
    cdef public dict[str, Variable] variables
    cdef public dict[str, Mesh] grids

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
        self.grids = {}

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

            elif block.blocktype == csdf.SDF_BLOCKTYPE_CONSTANT:
                self.variables[name] = make_Constant(name, block)

            elif block.blocktype in (
                    csdf.SDF_BLOCKTYPE_PLAIN_MESH,
                    csdf.SDF_BLOCKTYPE_POINT_MESH,
                    csdf.SDF_BLOCKTYPE_LAGRANGIAN_MESH
            ):
                grid_id = block.id.decode("UTF-8")
                self.grids[grid_id] = make_Mesh_from_sdf_block(name, block)

                if block.blocktype != csdf.SDF_BLOCKTYPE_POINT_MESH:
                    # Make the corresponding grid at mid-points, except for particle grids
                    mid_grid_block = make_Mesh_from_sdf_block(f"{name}_mid", block)
                    mid_grid_block.dims = tuple(dim - 1 for dim in mid_grid_block.dims if dim > 1)
                    mid_grid_block.parent = self.grids[grid_id]
                    self.grids[f"{grid_id}_mid"] = mid_grid_block

            elif block.blocktype in (
                    csdf.SDF_BLOCKTYPE_PLAIN_VARIABLE,
                    csdf.SDF_BLOCKTYPE_PLAIN_DERIVED,
                    csdf.SDF_BLOCKTYPE_POINT_VARIABLE,
                    csdf.SDF_BLOCKTYPE_POINT_DERIVED,
                    csdf.SDF_BLOCKTYPE_ARRAY,
            ):
                # If the block doesn't have a datatype, that probably
                # means its actually a grid dimension
                if block.datatype_out != 0:
                    self.variables[name] = make_Variable_from_sdf_block(name, block)

            block = block.next

    cpdef cnp.ndarray read(self, name: str):
        """Read a variable from the file, returning numpy array
        """

        cdef csdf.sdf_block_t* block = csdf.sdf_find_block_by_name(
            self._c_sdf_file, name.encode("utf-8")
        )

        if block is NULL:
            raise ValueError(f"Could not read variable '{name}'")

        var = self.variables[name]
        var_array = np.empty(var.dims, dtype=np.dtype(var.dtype), order="F")

        self._c_sdf_file.current_block = block
        csdf.sdf_helper_read_data(self._c_sdf_file, block)

        cdef void* data = (
            block.grids[0]
            if (block.grids is not NULL and block.grids[0] is not NULL)
            else block.data
        )

        # This is not as efficient as it could be -- we should be able
        # to steal the block's data, but I've not worked out to do
        # that properly yet. This is correct at least, and means we
        # don't need to worry about freeing the memory
        memcpy(cnp.PyArray_DATA(var_array), data, var_array.nbytes)

        return var_array

    def close(self):
        csdf.sdf_stack_destroy(self._c_sdf_file)
        csdf.sdf_close(self._c_sdf_file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
