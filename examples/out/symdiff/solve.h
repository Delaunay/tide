#ifndef SYMDIFF_SOLVE_HEADER
#define SYMDIFF_SOLVE_HEADER

#include "kiwi"
#include "expression.h"
#include <cmath>

namespace symdiff::solve {

void counter (Expression t, Expression v);
Expression solve (Expression function, int value, bool show_steps);

} // symdiff::solve
#endif