#ifndef SYMDIFF_SOLVE_HEADER
#define SYMDIFF_SOLVE_HEADER

#include "Expression.h"
#include "math.h"

namespace symdiff::solve {

void counter (Expression t, Expression v);
Expression solve (Expression function, int value, bool show_steps);

} // symdiff::solve
#endif