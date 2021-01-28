#include "tsp.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>

namespace py = pybind11;

PYBIND11_PLUGIN(pytsp) {
    py::module m("pytsp", "Algorithms to solve TSP.");
    m.def("random_distance_matrix", &tsp::randomDistanceMatrix);
    m.def("neighbor_matrix", &tsp::neighborMatrix);

    {
      auto submodule = m.def_submodule("heuristic_nearest");
      submodule.def("solve", &tsp::heuristic_nearest::solve);
    }

    {
      auto submodule = m.def_submodule("dynamic_programming");
      submodule.def("solve", &tsp::dynamic_programming::solve);
      submodule.def("solve_with_heuristic", &tsp::dynamic_programming::solveWithHeuristic);
    }

    {
      auto submodule = m.def_submodule("brute_force");
      submodule.def("solve", &tsp::brute_force::solve);
    }
}
