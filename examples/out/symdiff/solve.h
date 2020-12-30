#ifndef SYMDIFF_SOLVE_HEADER
#define SYMDIFF_SOLVE_HEADER

#include "kiwi"
extern auto __author__;
#include "expression.h"
#include <cmath>

namespace symdiff::solve {

void counter (Expression t, Expression v);
void solve (Expression function, int value, bool show_steps);
extern auto x;
extern auto y;
extern auto f1;
extern auto sol;
extern auto f2;

} // symdiff::solve
#endif