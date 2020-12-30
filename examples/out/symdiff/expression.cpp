#include "expression.h"
auto __author__ = "Pierre Delaunay";

namespace symdiff::expression {

Expression::Expression () {

}
void Expression::visit () {
  throw None;
}
void Expression::__repr__ () {
  return "FAIL";
}
void Expression::__str__ () {

}
void Expression::operator == (Expression* other) {
      if (this == other) {
      return true;
    };
  return false;
}
void Expression::derivate (str x) {
  " derivate in respect of x";
  return this;
}
void Expression::is_scalar () {
  return false;
}
void Expression::is_one () {
  return false;
}
void Expression::is_nul () {
  return false;
}
void Expression::is_leaf () {
  return false;
}
void Expression::eval (Dict<"Expression*", "Expression*"> variables) {
  " partially evaluate the expression";
}
void Expression::full_eval (Dict<"Expression*", "Expression*"> variables) {
  " fully evaluate the expression, every unknown must be specified";
}
void Expression::operator * (Expression* other) {
  return apply_operator(this, other, mult);
}
void Expression::operator + (Expression* other) {
  return apply_operator(this, other, add);
}
void Expression::__truediv__ (Expression* other) {
  return apply_operator(this, other, div);
}
void Expression::__pow__ (Expression* other) {
  return apply_operator(this, other, pow);
}
void Expression::operator - (Expression* other) {
  return apply_operator(this, other, sub);
}
void Expression::__neg__ () {
  " return - self";
  return mult(minus_one(), this);
}
void Expression::variables () {
  " Return a set of unknown the expression depend of";
  return set();
}
void Expression::get_tree () {
  " Return Operation tree";
  return std::make_array();
}
void Expression::apply_function (str function) {
  " apply a function to the graph ";
  return this;
}
void Expression::copy () {
  " return a copy of the expression";
  return this->apply_function("copy");
}
void Expression::simplify () {
  return this->apply_function("simplify");
}
void Expression::develop () {
  return this->apply_function("develop");
}
void Expression::factorize () {
  return this->apply_function("factorize");
}
void Expression::cancel () {
  " return the expression cancelling the current expression
            i.e x => 1/x     exp => log    x ** 2 => x ** 0.5 ";
  return this;
}
void Expression::_print () {
      if (this->is_leaf()) {
      return this->__str__();
    };
  return "(" + this->__str__() + ")";
}
void Expression::_id () {
  throw None;
}
void Expression::operator < (Expression* other) {
  return this->_id() < other._id();
}
void reorder (Expression* a, Expression* b) {
  auto ia = a._id();
  auto ib = b._id();
    if (ia < ib) {
    return std::make_tuple(a, b);
  };
    if (ia != ib) {
    return std::make_tuple(b, a);
  };
    if (a.is_scalar() && b.is_scalar() && a.value > b.value) {
    return std::make_tuple(b, a);
  };
  return std::make_tuple(a, b);
}
UnaryOperator::UnaryOperator (Expression* expr) {
  Expression.__init__(this);
  this->expr = expr;
}
void UnaryOperator::operator == (Expression* other) {
      if (this == other) {
      return true;
    };
      if (isinstance(other, type(this))) {
            if (this->expr == other.expr) {
        return true;
      };
    };
  return false;
}
void UnaryOperator::variables () {
  return this->expr.variables();
}
void UnaryOperator::get_tree () {
  return std::make_array(this) + this->expr.get_tree();
}
BinaryOperator::BinaryOperator (Expression* left, Expression* right) {
  Expression.__init__(this);
  this->left = left;
  this->right = right;
}
void BinaryOperator::operator == (Expression* other) {
      if (this == other) {
      return true;
    };
      if (isinstance(other, type(this))) {
            if (this->left == other.left && this->right == other.right) {
        return true;
      };
    };
  return false;
}
void BinaryOperator::variables () {
  return this->left.variables().union(this->right.variables());
}
void BinaryOperator::get_tree () {
  return std::make_array(this) + this->left.get_tree() + this->right.get_tree();
}
ScalarReal::ScalarReal (float value) {
  Expression.__init__(this);
  this->value = value;
}
void ScalarReal::__str__ () {
  return str(this->value);
}
void ScalarReal::__repr__ () {
  return "Scalar<" + str(this->value) + ">";
}
void ScalarReal::__neg__ () {
  return scalar(- this->value);
}
void ScalarReal::operator == (Expression* other) {
      if (this == other) {
      return true;
    };
      if (isinstance(other, ScalarReal) && other.value == this->value) {
      return true;
    };
  return false;
}
void ScalarReal::is_scalar () {
  return true;
}
void ScalarReal::is_one () {
  return this->value == 1;
}
void ScalarReal::is_nul () {
  return this->value == 0;
}
void ScalarReal::is_leaf () {
  return true;
}
void ScalarReal::derivate (Expression* x) {
  return zero();
}
void ScalarReal::eval (Dict<"Expression*", "Expression*"> variables) {
      if (this->is_one()) {
      return one();
    };
      if (this->is_nul()) {
      return zero();
    };
  return this;
}
void ScalarReal::full_eval (Dict<"Expression*", "Expression*"> variables) {
  return this->value;
}
void ScalarReal::apply_function (str function) {
  return scalar(this->value);
}
void ScalarReal::_id () {
  return 0;
}
Expression* __one = ScalarReal(1);
Expression* __zero = ScalarReal(0);
Expression* __minus_one = ScalarReal(- 1);
Expression* __two = ScalarReal(2);
void one () {
  return __one;
}
void zero () {
  return __zero;
}
void minus_one () {
  return __minus_one;
}
void two () {
  return __two;
}
Unknown::Unknown (str name, tuple size) {
  Expression.__init__(this);
  this->name = name;
  this->size = size;
}
void Unknown::__repr__ () {
  return this->name + str(this->size);
}
void Unknown::__hash__ () {
  return str.__hash__(this->name);
}
void Unknown::__str__ () {
  return this->name;
}
void Unknown::_id () {
  return 1;
}
void Unknown::is_leaf () {
  return true;
}
void Unknown::derivate (Expression* x) {
      if (x == this) {
      return one();
    };
  return zero();
}
void Unknown::eval (Dict<"Expression*", "Expression*"> variables) {
      if (contains(this, variables)) {
      return variables;
    };
  return this;
}
void Unknown::full_eval (Dict<"Expression*", "Expression*"> variables) {
  return variables.full_eval(variables);
}
void Unknown::variables () {
  return std::make_setthis;
}
Addition::Addition (Expression* left, Expression* right) {
  BinaryOperator.__init__(this, left, right);
}
void Addition::__str__ () {
  return str(this->left) + " + " + str(this->right);
}
void Addition::__repr__ () {
  return "+";
}
void Addition::derivate (Expression* x) {
  return add(this->left.derivate(x), this->right.derivate(x));
}
void Addition::eval (Dict<"Expression*", "Expression*"> variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return scalar(l.value + r.value);
    };
  return add(l, r);
}
void Addition::full_eval (Dict<"Expression*", "Expression*"> variables) {
  return this->left.full_eval(variables) + this->right.full_eval(variables);
}
void Addition::apply_function (str function) {
  return add(getattr(this->left, function)(), getattr(this->right, function)());
}
void Addition::_id () {
  return 2;
}
Subtraction::Subtraction (Expression* left, Expression* right) {
  BinaryOperator.__init__(this, left, right);
}
void Subtraction::__str__ () {
  return str(this->left) + " - " + str(this->right);
}
void Subtraction::__repr__ () {
  return "-";
}
void Subtraction::derivate (Expression* x) {
  return sub(this->left.derivate(x), this->right.derivate(x));
}
void Subtraction::eval (Dict<"Expression*", "Expression*"> variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return ScalarReal(l.value - r.value);
    };
  return sub(l, r);
}
void Subtraction::full_eval (Dict<"Expression*", "Expression*"> variables) {
  return this->left.full_eval(variables) - this->right.full_eval(variables);
}
void Subtraction::apply_function (str function) {
  return sub(getattr(this->left, function)(), getattr(this->right, function)());
}
void Subtraction::_id () {
  return 3;
}
Multiplication::Multiplication (Expression* left, Expression* right) {
  BinaryOperator.__init__(this, left, right);
}
void Multiplication::__str__ () {
  return this->left._print() + " * " + this->right._print();
}
void Multiplication::__repr__ () {
  return "*";
}
void Multiplication::derivate (Expression* x) {
  return add(mult(this->left, this->right.derivate(x)), mult(this->right, this->left.derivate(x)));
}
void Multiplication::eval (Dict<"Expression*", "Expression*"> variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return scalar(l.value * r.value);
    };
  return mult(l, r);
}
void Multiplication::full_eval (Dict<"Expression*", "Expression*"> variables) {
  return this->left.full_eval(variables) * this->right.full_eval(variables);
}
void Multiplication::apply_function (str function) {
  return mult(getattr(this->left, function)(), getattr(this->right, function)());
}
void Multiplication::copy () {
  return this->apply_function("copy");
}
void Multiplication::simplify () {
  return this->apply_function("simplify");
}
void Multiplication::develop () {
      if (isinstance(this->right, Addition)) {
      return this->left * this->right.left + this->left * this->right.right;
    };
      if (isinstance(this->left, Addition)) {
      return this->right * this->left.left + this->right * this->left.right;
    };
}
void Multiplication::_id () {
  return 4;
}
Exp::Exp (Expression* expr) {
  UnaryOperator.__init__(this, expr);
}
void Exp::__str__ () {
  return "exp(" + str(this->expr) + ")";
}
void Exp::__repr__ () {
  return "exp";
}
void Exp::derivate (Expression* x) {
  return mult(this->expr.derivate(x), this);
}
void Exp::eval (Dict<"Expression*", "Expression*"> variables) {
  auto l = this->expr.eval(variables);
      if (l.is_scalar()) {
      return scalar(math.exp(l.value));
    };
  return exp(l);
}
void Exp::full_eval (Dict<"Expression*", "Expression*"> variables) {
  return math.exp(this->expr.full_eval(variables));
}
void Exp::apply_function (str function) {
  return exp(getattr(this->expr, function)());
}
void Exp::cancel () {
  return log(this->expr);
}
void Exp::_id () {
  return 5;
}
Log::Log (Expression* expr) {
  UnaryOperator.__init__(this, expr);
}
void Log::__str__ () {
  return "log(" + str(this->expr) + ")";
}
void Log::__repr__ () {
  return "log";
}
void Log::derivate (Expression* x) {
  return div(this->expr.derivate(x), this->expr);
}
void Log::eval (Dict<"Expression*", "Expression*"> variables) {
  auto l = this->expr.eval(variables);
      if (l.is_scalar()) {
      return scalar(math.log(l.value));
    };
  return log(l.value);
}
void Log::full_eval (Dict<"Expression*", "Expression*"> variables) {
  return math.log(this->expr.full_eval(variables));
}
void Log::apply_function (str function) {
  return log(getattr(this->expr, function)());
}
void Log::cancel () {
  return exp(this->expr);
}
void Log::_id () {
  return 6;
}
Divide::Divide (Expression* up, Expression* down) {
  BinaryOperator.__init__(this, up, down);
}
void Divide::__str__ () {
  return this->left._print() + " / " + this->right._print();
}
void Divide::__repr__ () {
  return "/";
}
void Divide::up () {
  return this->left;
}
void Divide::down () {
  return this->right;
}
void Divide::derivate (Expression* x) {
  auto a = mult(this->right, this->left.derivate(x));
  auto b = mult(this->left, this->right.derivate(x));
  return div(sub(a, b), pow(this->right, scalar(2)));
}
void Divide::eval (Dict<"Expression*", "Expression*"> variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return scalar(l.value / r.value);
    };
  return div(l, r);
}
void Divide::full_eval (Dict<"Expression*", "Expression*"> variables) {
  return this->left.full_eval(variables) / this->right.full_eval(variables);
}
void Divide::apply_function (str function) {
  return div(getattr(this->left, function)(), getattr(this->right, function)());
}
void Divide::_id () {
  return 7;
}
Pow::Pow (Expression* expr, Expression* power) {
  BinaryOperator.__init__(this, expr, power);
}
void Pow::power () {
  return this->right;
}
void Pow::expr () {
  return this->left;
}
void Pow::__str__ () {
  return this->left._print() + " ^ " + this->right._print();
}
void Pow::__repr__ () {
  return "^";
}
void Pow::derivate (Expression* x) {
  return mult(mult(this->power(), this->expr().derivate(x)), pow(this->expr(), add(this->power(), minus_one())));
}
void Pow::eval (Dict<"Expression*", "Expression*"> variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return scalar(pow(l.value, r.value));
    };
  return pow(l, r);
}
void Pow::full_eval (Dict<"Expression*", "Expression*"> variables) {
  return pow(this->left.full_eval(variables), this->right.full_eval(variables));
}
void Pow::apply_function (str function) {
  return pow(getattr(this->left, function)(), getattr(this->right, function)());
}
void Pow::_id () {
  return 8;
}
MathConstant::MathConstant (str name, float value) {
  ScalarReal.__init__(this, value);
  this->name = name;
}
void MathConstant::__str__ () {
  return this->name;
}
void MathConstant::__repr__ () {
  return this->name;
}
void MathConstant::copy () {
  return this;
}
void MathConstant::_id () {
  return 9;
}
auto __euler = MathConstant("e", 2.718281828459045);
auto __pi = MathConstant("pi", 3.141592653589793);
void pi () {
  return __pi;
}
void e () {
  return __euler;
}
void add (Expression* l, Expression* r) {
  std::make_tuple(l, r) = reorder(l, r);
    if (l.is_nul()) {
    return r;
  };
    if (r.is_scalar() && l.is_scalar()) {
    return scalar(r.value + l.value);
  };
    if (l == r) {
    return mult(l, scalar(2));
  };
    if (isinstance(l, Subtraction)) {
        if (l.right == r) {
      return l.left;
    };
  };
    if (isinstance(r, Subtraction)) {
        if (r.right == l) {
      return r.left;
    };
  };
    if (isinstance(l, Multiplication)) {
        if (l.right == r && l.left.is_scalar()) {
      return mult(r, scalar(l.left.value + 1));
    };
        if (l.left == r && l.right.is_scalar()) {
      return mult(r, scalar(l.right.value + 1));
    };
  };
    if (isinstance(r, Multiplication)) {
        if (r.right == l && r.left.is_scalar()) {
      return mult(l, scalar(r.left.value + 1));
    };
        if (r.left == l && r.right.is_scalar()) {
      return mult(l, scalar(r.right.value + 1));
    };
  };
  return Addition(l, r);
}
void mult (Expression* l, Expression* r) {
  std::make_tuple(l, r) = reorder(l, r);
    if (l.is_nul() || r.is_nul()) {
    return zero();
  };
    if (r.is_one()) {
    return l;
  };
    if (l.is_one()) {
    return r;
  };
    if (l.is_scalar() && r.is_scalar()) {
    return scalar(l.value * r.value);
  };
    if (l == r) {
    return pow(l, scalar(2));
  };
    if (l.is_scalar() && isinstance(r, Multiplication)) {
        if (r.left.is_scalar()) {
      return mult(scalar(l.value * r.left.value), r.right);
    };
  };
    if (isinstance(l, Divide)) {
        if (l.down() == r) {
      return l.up();
    };
  };
    if (isinstance(r, Divide)) {
        if (r.down() == l) {
      return r.up();
    };
  };
    if (isinstance(l, Pow)) {
        if (l.left == r && l.right.is_scalar()) {
      return pow(r, scalar(l.right.value + 1));
    };
  };
    if (isinstance(r, Pow)) {
        if (r.left == l && r.right.is_scalar()) {
      return pow(l, scalar(r.right.value + 1));
    };
  };
  return Multiplication(l, r);
}
void exp (Expression* expr) {
    if (expr.is_nul()) {
    return one();
  };
    if (expr.is_one()) {
    return e();
  };
    if (isinstance(expr, Log)) {
    return expr.expr;
  };
  return Exp(expr);
}
void pow (Expression* expr, Expression* power) {
    if (power.is_nul()) {
    return one();
  };
    if (expr.is_nul()) {
    return zero();
  };
    if (power.is_one()) {
    return expr;
  };
    if (isinstance(expr, Pow)) {
    return pow(expr.expr(), expr.power() * power);
  };
  return Pow(expr, power);
}
void log (Expression* expr) {
    if (expr.is_one()) {
    return zero();
  };
    if (expr == e()) {
    return one();
  };
    if (isinstance(expr, Exp)) {
    return expr.expr;
  };
  return Log(expr);
}
void div (Expression* up, Expression* down) {
    if (down.is_one()) {
    return up;
  };
    if (up == down) {
    return one();
  };
    if (up.is_nul()) {
    return zero();
  };
    if (up.is_scalar() && down.is_scalar()) {
    auto rv = down.value;
    auto lv = up.value;
        if (rv - int(rv) == 0 && lv - int(lv) == 0) {
      auto gcd = math.gcd(int(rv), int(lv));
      rv /= gcd;
      lv /= gcd;
      auto up = scalar(lv);
      auto down = scalar(rv);
    } else {
      return scalar(lv / rv);
    };
  };
    if (isinstance(up, Multiplication)) {
        if (up.left == down) {
      return up.right;
    };
        if (up.right == down) {
      return up.left;
    };
  };
    if (isinstance(down, Multiplication)) {
        if (down.left == up) {
      return down.right;
    };
        if (down.right == up) {
      return down.left;
    };
  };
  return Divide(up, down);
}
void scalar (float v) {
    if (v == 0) {
    return zero();
  };
    if (v == 1) {
    return one();
  };
    if (v == - 1) {
    return minus_one();
  };
    if (v == 2) {
    return two();
  };
  return ScalarReal(v);
}
void sub (Expression* l, Expression* r) {
    if (l == r) {
    return zero();
  };
    if (l.is_nul()) {
    return - r;
  };
    if (r.is_nul()) {
    return l;
  };
    if (r.is_scalar() && l.is_scalar()) {
    return scalar(l.value - r.value);
  };
    if (isinstance(l, Addition)) {
        if (r == l.right) {
      return l.left;
    };
        if (r == l.left) {
      return l.right;
    };
  };
  return Subtraction(l, r);
}
int __main__(int argc, const char* argv[]) {
  auto x = Unknown("x");
  auto y = Unknown("y");
  auto val = std::make_dict{{ x, scalar(5) }};
  auto f = pow(x, 3) - pow(y, 2);
  auto dfdx = f.derivate(x);
  print(" f   : ", f, "	Eval: ", f.eval(val));
  print("dfdx : ", dfdx, "	Eval: ", dfdx.eval(val));
  auto val = std::make_dict{{ x, scalar(5) }, { y, scalar(2) }};
  print(" f   : ", f, "	Eval: ", f.full_eval(val));
  print("dfdx : ", dfdx, "	Eval: ", dfdx.full_eval(val));
  return 0;
}

} // symdiff::expression