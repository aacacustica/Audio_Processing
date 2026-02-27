#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "utils.hpp"

namespace py = pybind11;


// -- Wrapers :  Numpy -> Nc ( copia simple, asumiendo C-contiguous) ---- //

static nc::NdArray<float> to_nc_1d(const py::array_t<float, py::array::c_style | py::array::forcecast>& arr)
{

    auto buf = arr.request();
    std::size_t N = 0;
    if (buf.ndim == 1){
        N = static_cast<std::size_t>(buf.shape[0]);

    }else if (buf.ndim == 2){
        const auto r =  static_cast<std::size_t>(buf.shape[0]);
        const auto c =  static_cast<std::size_t>(buf.shape[1]);

        if (r == 1) N = c;
        else if (c == 1) N = r;
        else throw std::invalid_argument("Expected vector shape (N,), (N,1) or (1,N).");
    }else{
        throw std::invalid_argument(
            "Expected vector as 1D/2D array. Got ndim=" + std::to_string(buf.ndim) +
            " shape0=" + (buf.ndim >= 1 ? std::to_string(buf.shape[0]) : std::string("NA")) +
            " shape1=" + (buf.ndim >= 2 ? std::to_string(buf.shape[1]) : std::string("NA"))
        );    
    }

    auto* ptr = static_cast<float*>(buf.ptr);
    
    nc::NdArray<float> out = nc::zeros<float>(1, N);
    for (std::size_t i = 0; i < N; ++i) out(0, i) = ptr[i];

    return out;
}

static nc::NdArray<float> to_nc_2d(const py::array_t<float, py::array::c_style | py::array::forcecast>& arr)
{
    auto buf = arr.request();
    if (buf.ndim != 2) throw std::invalid_argument("Expected 2D float32 array.");

    const float* ptr = static_cast<const float*>(buf.ptr);
    const std::size_t r = static_cast<std::size_t>(buf.shape[0]);
    const std::size_t c = static_cast<std::size_t>(buf.shape[1]);

    nc::NdArray<float> out = nc::zeros<float>(r, c);
    // row-major copy
    for (std::size_t i = 0; i < r; ++i)
        for (std::size_t j = 0; j < c; ++j)
            out(i, j) = ptr[i * c + j];

    return out;
}

// Nc -> NumPy (copia) ---- //
static py::array_t<float> to_np_1d(const nc::NdArray<float>& a)
{
    py::array_t<float> out(a.size());
    auto buf = out.request();
    auto* ptr = static_cast<float*>(buf.ptr);

    for(std::size_t i = 0; i < a.size(); ++i){ ptr[i] = a(0,i);}

    return out;
}


static py::array_t<float> to_np_2d(const nc::NdArray<float>& a)
{
    const std::size_t r = a.numRows();
    const std::size_t c = a.numCols();

    py::array_t<float> out({r, c});   // <-- {rows, cols}
    auto buf = out.request();
    float* ptr = static_cast<float*>(buf.ptr);

    for (std::size_t i = 0; i < r; ++i)
        for (std::size_t j = 0; j < c; ++j)
            ptr[i*c + j] = a(i,j);

    return out;
}


// ---- wrappers expuestos a Python ----
static float get_level_db_py(py::array_t<float, py::array::c_style | py::array::forcecast> x, float C)
{
    return get_level_db(to_nc_1d(x), C);
}

static py::tuple lfilter_np_py(py::array_t<float, py::array::c_style | py::array::forcecast> b,
                               py::array_t<float, py::array::c_style | py::array::forcecast> a,
                               py::array_t<float, py::array::c_style | py::array::forcecast> x,
                               py::object zi_obj)
{
    const auto bb = to_nc_1d(b);
    const auto aa = to_nc_1d(a);
    const auto xx = to_nc_1d(x);

    nc::NdArray<float> zi;
    if (zi_obj.is_none()) {
        zi = nc::NdArray<float>(); // vacío -> lfilter lo interpreta como zi.size()==0
    } else {
        zi = to_nc_1d(zi_obj.cast<py::array_t<float, py::array::c_style | py::array::forcecast>>());
    }

    auto [y, zf] = lfilter_np(bb, aa, xx, zi);
    return py::make_tuple(to_np_1d(y), to_np_1d(zf));
}



static py::tuple sosfilt_np_py(py::array_t<float, py::array::c_style | py::array::forcecast> sos,
                               py::array_t<float, py::array::c_style | py::array::forcecast> x,
                               py::object zi_obj)
{
    const auto ss = to_nc_2d(sos);
    const auto xx = to_nc_1d(x);

    nc::NdArray<float> zi;
    if (zi_obj.is_none()) {
        zi = nc::NdArray<float>();
    } else {
        zi = to_nc_2d(zi_obj.cast<py::array_t<float, py::array::c_style | py::array::forcecast>>());
    }

    auto [y, zf] = sosfilt_np(ss, xx, zi);
    // y es 1D, zf es 2D (nsec,2)
    return py::make_tuple(to_np_1d(y), to_np_2d(zf));
}


PYBIND11_MODULE(leq_levels_oct_weighting_C, m) {
    m.doc() = "C++17 module for Leq level octave weighting calculations";
    m.def("get_level_db", &get_level_db_py, py::arg("x"), py::arg("C"));
    m.def("lfilter_np", &lfilter_np_py,
          py::arg("b"), py::arg("a"), py::arg("x"), py::arg("zi") = py::none());
    m.def("sosfilt_np", &sosfilt_np_py,
          py::arg("sos"), py::arg("x"), py::arg("zi") = py::none());
}