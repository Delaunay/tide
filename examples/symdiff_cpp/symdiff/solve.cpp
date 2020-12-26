#include "solve.h"

namespace symdiff::solve {

void counter (Expression t, Expression v) {
    if (isinstance(v, Multiplication)) {
    return std::tuple<>{div(t, v.right), v.left, true};
  };
    if (isinstance(v, Addition)) {
    return std::tuple<>{sub(t, v.right), v.left, true};
  };
    if (isinstance(v, Divide)) {
    return std::tuple<>{mult(t, v.right), v.left, true};
  };
    if (isinstance(v, Subtraction)) {
    return std::tuple<>{add(t, v.right), v.left, true};
  };
    if (isinstance(v, Exp)) {
    return std::tuple<>{log(t), v.expr, true};
  };
    if (isinstance(v, Log)) {
    return std::tuple<>{exp(t), v.expr, true};
  };
    if (isinstance(v, Pow)) {
    return std::tuple<>{pow(t, div(one(), v.power())), v.expr(), true};
  };
  return std::tuple<>{t, v, false};
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
    std::tuple<>{s, f, c} = counter(s, f);
  };
  return s;
}

} // symdiff::solve