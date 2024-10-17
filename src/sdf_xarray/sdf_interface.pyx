cimport csdf

import dataclasses
import re
import time

from libc.string cimport memcpy

import numpy as np

cimport numpy as cnp

cnp.import_array()

# Some systems don't have F128
_NUMPY_128 = getattr(np, "float128", None)

cdef list[cnp.dtype | None] _sdf_type_mapping = [
    None,
    cnp.dtype(np.int32),
    cnp.dtype(np.int64),
    cnp.dtype(np.float32),
    cnp.dtype(np.float64),
    _NUMPY_128,
    cnp.dtype("S"),
    cnp.dtype(np.bool_),
]


@dataclasses.dataclass
cdef class Block:
    _id: str
    name: str
    dtype: np.dtype
    shape: tuple[int]
    is_point_data: bool
    sdffile: SDFFile | None


@dataclasses.dataclass
cdef class Variable(Block):
    units: tuple[str] | None
    mult: float | None
    grid: str | None
    grid_mid: str | None

    @property
    def data(self) -> np.ndarray :
        """Read a variable from the file, returning numpy array
        """

        return self.sdffile.read(self)

    @staticmethod
    cdef Variable from_block(str name, csdf.sdf_block_t* block, SDFFile sdffile):
        return Variable(
            _id=block.id.decode("UTF-8"),
            name=name,
            dtype=_sdf_type_mapping[block.datatype_out],
            shape=tuple(block.dims[i] for i in range(block.ndims)),
            units=block.units.decode("UTF-8") if block.units else None,
            mult=block.mult if block.mult else None,
            grid=block.mesh_id.decode("UTF-8") if block.mesh_id else None,
            grid_mid=f"{block.mesh_id.decode('UTF-8')}_mid" if block.mesh_id else None,
            is_point_data=block.blocktype == csdf.SDF_BLOCKTYPE_POINT_VARIABLE,
            sdffile=sdffile,
        )


@dataclasses.dataclass
cdef class Mesh(Block):
    units: tuple[str]
    labels: tuple[str]
    mults: tuple[float] | None
    parent: Mesh | None = None

    @property
    def data(self) -> tuple[np.ndarray]:
        """Read a variable from the file, returning numpy array
        """

        return self.sdffile.read(self)

    @staticmethod
    cdef Mesh from_block(str name, csdf.sdf_block_t* block, SDFFile sdffile):
        return Mesh(
            _id=block.id.decode("UTF-8"),
            name=name,
            dtype=_sdf_type_mapping[block.datatype_out],
            shape=tuple(block.dims[i] for i in range(block.ndims)),
            units=tuple(
                block.dim_units[i].decode("UTF-8") for i in range(block.ndims)
            ),
            labels=tuple(
                block.dim_labels[i].decode("UTF-8") for i in range(block.ndims)
            ),
            mults=(
                tuple(block.dim_mults[i] for i in range(block.ndims))
                if block.dim_mults
                else None
            ),
            is_point_data=block.blocktype == csdf.SDF_BLOCKTYPE_POINT_MESH,
            sdffile=sdffile,
        )


_CONSTANT_UNITS_RE = re.compile(r"(?P<name>.*) \((?P<units>.*)\)$")

@dataclasses.dataclass
cdef class Constant:
    _id: str
    name: str
    data: int | str | float
    units: str | None

    @staticmethod
    cdef Constant from_block(str name, csdf.sdf_block_t* block):
        data: int | str | float | double

        if block.datatype == csdf.SDF_DATATYPE_REAL4:
            data = (<float*>block.const_value)[0]
        elif block.datatype == csdf.SDF_DATATYPE_REAL8:
            data = (<double*>block.const_value)[0]
        if block.datatype == csdf.SDF_DATATYPE_INTEGER4:
            data = (<csdf.int32_t*>block.const_value)[0]
        if block.datatype == csdf.SDF_DATATYPE_INTEGER8:
            data = (<csdf.int64_t*>block.const_value)[0]

        # There's no metadata with e.g. units, but there's a
        # convention to put one in brackets at the end of the name,
        # if so, strip it off to give the name and units
        units = None
        if match := _CONSTANT_UNITS_RE.match(name):
            name = match["name"]
            units = match["units"]

        return Constant(
            _id=block.id.decode("UTF-8"), name=name, data=data, units=units
        )

    @property
    def is_point_data(self) -> bool:
        return False


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
                # We modify the name to remove units, so convert it
                # first so we can get the new name
                constant = Constant.from_block(name, block)
                self.variables[constant.name] = constant

            elif block.blocktype in (
                    csdf.SDF_BLOCKTYPE_PLAIN_MESH,
                    csdf.SDF_BLOCKTYPE_POINT_MESH,
                    csdf.SDF_BLOCKTYPE_LAGRANGIAN_MESH
            ):
                grid_id = block.id.decode("UTF-8")
                self.grids[grid_id] = Mesh.from_block(name, block, self)

                if block.blocktype != csdf.SDF_BLOCKTYPE_POINT_MESH:
                    # Make the corresponding grid at mid-points, except for
                    # particle grids
                    mid_grid_block = Mesh.from_block(f"{name}_mid", block, self)
                    mid_grid_block.shape = tuple(
                        dim - 1 for dim in mid_grid_block.shape if dim > 1
                    )
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
                    self.variables[name] = Variable.from_block(name, block, self)

            block = block.next

    cpdef read(self, var: Block):
        """Read a variable from the file, returning numpy array
        """

        if self._c_sdf_file is NULL:
            raise RuntimeError(
                f"Can't read '{var.name}', file '{self.filename}' is closed"
            )

        is_mesh: bool = isinstance(var, Mesh)

        # Has a parent block, so we need to average node data to midpoint
        if is_mesh and var.parent:
            return self._read_mid_grid(var)

        cdef csdf.sdf_block_t* block = csdf.sdf_find_block_by_name(
            self._c_sdf_file, var.name.encode("utf-8")
        )

        if block is NULL:
            raise RuntimeError(f"Could not read variable '{var.name}'")

        self._c_sdf_file.current_block = block
        csdf.sdf_helper_read_data(self._c_sdf_file, block)

        if is_mesh:
            # Meshes store the data for separate dimensions in block.grids
            if not (block.grids is not NULL and block.grids[0] is not NULL):
                raise RuntimeError(f"Could not read variable '{var.name}'")

            data = []
            for i, dim in enumerate(var.shape):
                data.append(
                    self._make_array((dim,), var.dtype, block.grids[i])
                )
            return tuple(data)

        # Normal variables
        return self._make_array(var.shape, var.dtype, block.data)

    cdef _read_mid_grid(self, mesh: Mesh):
        """Read a midpoint grid"""

        data = []
        for dim in mesh.parent.data:
            if len(dim.shape) == 1:
                mid_point = (dim[:-1] + dim[1:]) / 2
            elif len(dim.shape) == 2:
                mid_point = (
                    dim[:-1, :-1] + dim[1:, :-1] + dim[:-1, 1:] + dim[1:, 1:]
                ) / 4
            else:
                raise ValueError(
                    f"Unexpected number of dimensions reading mesh '{mesh.name}' "
                    f"(expected 1 or 2, got {len(dim.shape)})"
                )
            data.append(mid_point)
        return tuple(data)

    cdef cnp.ndarray _make_array(
        self, tuple[int, ...] dims, cnp.dtype dtype, void* data
    ):
        """Helper function for making Numpy arrays from data allocated elsewhere"""
        # This is not as efficient as it could be -- we should be able to steal
        # the block's data, but I've not worked out to do that properly
        # yet. This is correct at least, and means we don't need to worry about
        # freeing the memory. Can't just use PyArray_NewFromDescr because this
        # isn't available from Cython. Might be able to use one of the other
        # low-level creation routines?
        var_array = np.empty(dims, dtype=dtype, order="F")
        memcpy(cnp.PyArray_DATA(var_array), data, var_array.nbytes)

        return var_array

    def close(self):
        if self._c_sdf_file is NULL:
            return
        csdf.sdf_stack_destroy(self._c_sdf_file)
        csdf.sdf_close(self._c_sdf_file)
        self._c_sdf_file = NULL

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
