#include "solve.h"

namespace symdiff::solve {

void counter (Expression t, Expression v) {
    if (isinstance(v, Multiplication)) {
    return std::make_tuple(div(t, v.right), v.left, true);
  };
    if (isinstance(v, Addition)) {
    return std::make_tuple(sub(t, v.right), v.left, true);
  };
    if (isinstance(v, Divide)) {
    return std::make_tuple(mult(t, v.right), v.left, true);
  };
    if (isinstance(v, Subtraction)) {
    return std::make_tuple(add(t, v.right), v.left, true);
  };
    if (isinstance(v, Exp)) {
    return std::make_tuple(log(t), v.expr, true);
  };
    if (isinstance(v, Log)) {
    return std::make_tuple(exp(t), v.expr, true);
  };
    if (isinstance(v, Pow)) {
    return std::make_tuple(pow(t, div(one(), v.power())), v.expr(), true);
  };
  return std::make_tuple(t, v, false);
}
Expression solve (Expression function, int value, bool show_steps) {
  " Solve trivial Expression ";
  auto f = function.copy();
  auto s = ScalarReal(value);
  auto c = true;
    while (c) {
      if (show_steps) {
      print(f, "=", s);
    };
    std::make_tuple(s, f, c) = counter(s, f);
  };
  return s;
}

} // symdiff::solve