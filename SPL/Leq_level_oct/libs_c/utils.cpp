#include <iostream>
#include <NumCpp.hpp>
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <tuple>


float PREF = 2e-6f;



float get_level_db(const nc::NdArray<float>& x, float C)
{

    float ms = 0.0f;
    for (auto v : x)
        ms += v * v;

    ms = ms / static_cast<float>(x.size()) + PREF;

    return 10.0f * std::log10(ms / (PREF * PREF)) + C;
}


std::tuple<nc::NdArray<float>, nc::NdArray<float>> lfilter_np(const nc::NdArray<float>& b, const nc::NdArray<float>& a, const nc::NdArray<float>& x, const nc::NdArray<float>& zi){


    std::size_t n = 0;
    nc::NdArray<float> y = nc::NdArray<float>();
    double a0 = 0;
    auto aa = a;
    auto bb = b; 
    nc::NdArray<float> z;
    const auto x_shape = x.shape();
    const auto x_rows = x_shape.rows;
    const auto x_cols = x_shape.cols;


    if (!(x_rows == 1 || x_cols == 1)) {
        throw std::invalid_argument("Input x must be a vector (1xN or Nx1). <---- Correct shape checking");
    }
        
    if (a.size() == 0 || b.size() == 0){
        throw std::invalid_argument("Filter coefficients a and b must be non-empty. ");
    }

    a0 = a[0];
    if (a0 ==  0){
        throw std::invalid_argument("First coefficient of 'a' must be non-zero. ");
    }
    if (a0 != 1.0){
        bb = nc::divide(b, static_cast<float>(a0));
        aa = nc::divide(a, static_cast<float>(a0));
    }
    n = std::max(aa.size(), bb.size()) - 1;

    if (zi.size() == 0) {
        z = nc::zeros<float>(1, n);
    } else {
        if (zi.size() != n) {
            throw std::invalid_argument("[lfilter.cpp] Initial state zi has incorrect length.");
        }
        z = zi;
    }

    
    y = nc::zeros<float>(1, x.size());

    double xi = 0;
    double y0 = 0;
    double bk = 0;
    double ak = 0;
    double bn = 0;
    double an = 0;

    for (int i = 0; i< x.size(); i++){
        
        xi = x(0,i);
        if (n == 0){
            y(0,i) = bb[0] * xi;
            continue;
        }
        y0 = bb[0] * xi + z(0,0);
        y(0,i) = y0;

        for (int k = 1; k < n; k++){
            bk = (k < bb.size()) ? bb[k] : 0.0f;
            ak = (k < aa.size()) ? aa[k] : 0.0f;
            z(0,k-1) = z(0,k) + bk * xi - ak * y0;
        }

        bn = (n < bb.size()) ? bb[n] : 0.0;
        an = (n < aa.size()) ? aa[n] : 0.0;
        z(0,n-1) = bn * xi - an * y0;
    }

    return {y, z};


}

std::tuple<nc::NdArray<float>, nc::NdArray<float>> sosfilt_np(const nc::NdArray<float>& sos, const nc::NdArray<float>& x, const nc::NdArray<float>& zi){

    int nsec = sos.numRows();
    nc::NdArray<float> y = x;
    nc::NdArray<float> z = nc::NdArray<float>();
    const auto sos_shape = sos.shape();
    const auto sos_rows = sos_shape.rows;
    const auto sos_cols = sos_shape.cols;

    const auto y_rows = y.numRows();
    const auto y_cols = y.numCols();

    if (!(y_rows == 1 || y_cols == 1)) {
        throw std::invalid_argument("x must be a vector (1xN or Nx1).");
    }




    if (zi.size() == 0) {
        z = nc::zeros<float>(nsec, 2);
    } else {

        if (zi.numRows() != nsec || zi.numCols() != 2) {
            throw std::invalid_argument(
                std::string("[sosfilt.cpp] Initial state zi must have shape (nsec, 2). Got (")
                + std::to_string(zi.numRows()) + "," + std::to_string(zi.numCols())
                + "), expected (" + std::to_string(nsec) + ",2)."
            );
        }
        z = zi;
    }

    if (sos.numRows() <= 0 ||sos.numCols() != 6) {
    throw std::invalid_argument("sos must have shape (nsec, 6).");
    }


    double b0=0,b1=0,b2=0,a0=0,a1=0,a2=0;
    double z1=0,z2=0;

    for(int s =0; s< nsec; s++){
        
        b0 = sos(s,0);
        b1 = sos(s,1);
        b2 = sos(s,2);
        a0 = sos(s,3);
        a1 = sos(s,4);
        a2 = sos(s,5);

        if (a0 != 1.0){
            if (a0 == 0.0) throw std::invalid_argument("a0 must be non-zero");
            b0 = b0 / a0;
            b1 = b1 / a0;
            b2 = b2 / a0;
            a1 = a1 / a0;
            a2 = a2 / a0;
        }

        z1 = z(s,0);
        z2 = z(s,1);

        double xn = 0;
        double yn = 0;

        nc::NdArray<float> out = (y_rows == 1)
            ? nc::zeros<float>(1, y_cols)
            : nc::zeros<float>(y_rows, 1);
        const std::size_t N = y.size();

    for (std::size_t i = 0; i < N; ++i) {
        xn = (y_rows == 1) ? y(0, i) : y(i, 0);
        yn = b0 * xn + z1;
        z1 = b1 * xn - a1 * yn + z2;
        z2 = b2 * xn - a2 * yn;

        if (y_rows == 1) out(0, i) = static_cast<float>(yn);
        else             out(i, 0) = static_cast<float>(yn);
    }

        y = out;
        z(s,0) =  static_cast<float>(z1);
        z(s,1) =  static_cast<float>(z2);
    }

    return {y,z}; 
}

