#include "expression.h"

namespace symdiff::expression {

_Expression::_Expression () {

}
str _Expression::__repr__ () {
  return "FAIL";
}
str _Expression::__str__ () {

}
bool _Expression::__eq__ (Expression other) {
      if (other == this) {
      return true;
    };
  return false;
}
Expression _Expression::derivate (str x) {
  " derivate in respect of x";
  return this;
}
bool _Expression::is_scalar () {
  return false;
}
bool _Expression::is_one () {
  return false;
}
bool _Expression::is_nul () {
  return false;
}
bool _Expression::is_leaf () {
  return false;
}
Expression _Expression::eval (Dict variables) {
  " partially evaluate the expression";
}
float _Expression::full_eval (Dict variables) {
  " fully evaluate the expression, every unknown must be specified";
}
Expression _Expression::__mul__ (Expression other) {
  return apply_operator(this, other, mult);
}
Expression _Expression::__add__ (Expression other) {
  return apply_operator(this, other, add);
}
Expression _Expression::__truediv__ (Expression other) {
  return apply_operator(this, other, div);
}
Expression _Expression::__pow__ (Expression other) {
  return apply_operator(this, other, pow);
}
Expression _Expression::__sub__ (Expression other) {
  return apply_operator(this, other, sub);
}
Expression _Expression::__neg__ () {
  " return - self";
  return mult(minus_one(), this);
}
void _Expression::variables () {
  " Return a set of unknown the expression depend of";
  return set();
}
void _Expression::get_tree () {
  " Return Operation tree";
  return std::make_array();
}
Expression _Expression::apply_function (str function) {
  " apply a function to the graph ";
  return this;
}
Expression _Expression::copy () {
  " return a copy of the expression";
  return this->apply_function("copy");
}
Expression _Expression::simplify () {
  return this->apply_function("simplify");
}
Expression _Expression::develop () {
  return this->apply_function("develop");
}
Expression _Expression::factorize () {
  return this->apply_function("factorize");
}
Expression _Expression::cancel () {
  " return the expression cancelling the current expression
            i.e x => 1/x     exp => log    x ** 2 => x ** 0.5 ";
  return this;
}
void _Expression::_print () {
      if (this->is_leaf()) {
      return this->__str__();
    };
  return "(" + this->__str__() + ")";
}
int _Expression::_id () {
  throw None;
}
bool _Expression::__lt__ (Expression other) {
  return other._id() < this->_id();
}
Tuple reorder (Expression a, Expression b) {
  auto ia = a._id();
  auto ib = b._id();
    if (ib < ia) {
    return std::make_tuple(a, b);
  };
    if (ib != ia) {
    return std::make_tuple(b, a);
  };
    if (a.is_scalar() && b.is_scalar() && b.value > a.value) {
    return std::make_tuple(b, a);
  };
  return std::make_tuple(a, b);
}
_UnaryOperator::_UnaryOperator (Expression expr) {
  Expression->__init__(this);
  this->expr = expr;
}
bool _UnaryOperator::__eq__ (Expression other) {
      if (other == this) {
      return true;
    };
      if (isinstance(other, type(this))) {
            if (other.expr == this->expr) {
        return true;
      };
    };
  return false;
}
void _UnaryOperator::variables () {
  return this->expr.variables();
}
void _UnaryOperator::get_tree () {
  return std::make_array(this) + this->expr.get_tree();
}
_BinaryOperator::_BinaryOperator (Expression left, Expression right) {
  Expression->__init__(this);
  this->left = left;
  this->right = right;
}
bool _BinaryOperator::__eq__ (Expression other) {
      if (other == this) {
      return true;
    };
      if (isinstance(other, type(this))) {
            if (other.left == this->left && other.right == this->right) {
        return true;
      };
    };
  return false;
}
void _BinaryOperator::variables () {
  return this->left.variables().union(this->right.variables());
}
void _BinaryOperator::get_tree () {
  return std::make_array(this) + this->left.get_tree() + this->right.get_tree();
}
_ScalarReal::_ScalarReal (float value) {
  Expression->__init__(this);
  this->value = value;
}
str _ScalarReal::__str__ () {
  return str(this->value);
}
str _ScalarReal::__repr__ () {
  return "Scalar<" + str(this->value) + ">";
}
Expression _ScalarReal::__neg__ () {
  return scalar(- this->value);
}
bool _ScalarReal::__eq__ (Expression other) {
      if (other == this) {
      return true;
    };
      if (isinstance(other, ScalarReal) && this->value == other.value) {
      return true;
    };
  return false;
}
bool _ScalarReal::is_scalar () {
  return true;
}
bool _ScalarReal::is_one () {
  return 1 == this->value;
}
bool _ScalarReal::is_nul () {
  return 0 == this->value;
}
bool _ScalarReal::is_leaf () {
  return true;
}
Expression _ScalarReal::derivate (Expression x) {
  return zero();
}
void _ScalarReal::eval (Dict variables) {
      if (this->is_one()) {
      return one();
    };
      if (this->is_nul()) {
      return zero();
    };
  return this;
}
Expression _ScalarReal::full_eval (Dict variables) {
  return this->value;
}
Expression _ScalarReal::apply_function (str function) {
  return scalar(this->value);
}
int _ScalarReal::_id () {
  return 0;
}
Expression one () {
  return __one;
}
Expression zero () {
  return __zero;
}
Expression minus_one () {
  return __minus_one;
}
Expression two () {
  return __two;
}
_Unknown::_Unknown (str name, tuple size) {
  Expression->__init__(this);
  this->name = name;
  this->size = size;
}
str _Unknown::__repr__ () {
  return this->name + str(this->size);
}
str _Unknown::__hash__ () {
  return str.__hash__(this->name);
}
str _Unknown::__str__ () {
  return this->name;
}
int _Unknown::_id () {
  return 1;
}
bool _Unknown::is_leaf () {
  return true;
}
Expression _Unknown::derivate (Expression x) {
      if (this == x) {
      return one();
    };
  return zero();
}
Expression _Unknown::eval (Dict variables) {
      if (contains(this, variables)) {
      return variables;
    };
  return this;
}
Expression _Unknown::full_eval (Dict variables) {
  return variables.full_eval(variables);
}
void _Unknown::variables () {
  return std::make_setthis;
}
_Addition::_Addition (Expression left, Expression right) {
  BinaryOperator->__init__(this, left, right);
}
str _Addition::__str__ () {
  return str(this->left) + " + " + str(this->right);
}
str _Addition::__repr__ () {
  return "+";
}
Expression _Addition::derivate (Expression x) {
  return add(this->left.derivate(x), this->right.derivate(x));
}
Expression _Addition::eval (Dict variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return scalar(l.value + r.value);
    };
  return add(l, r);
}
Expression _Addition::full_eval (Dict variables) {
  return this->left.full_eval(variables) + this->right.full_eval(variables);
}
void _Addition::apply_function (str function) {
  return add(getattr(this->left, function)(), getattr(this->right, function)());
}
int _Addition::_id () {
  return 2;
}
_Subtraction::_Subtraction (Expression left, Expression right) {
  BinaryOperator->__init__(this, left, right);
}
str _Subtraction::__str__ () {
  return str(this->left) + " - " + str(this->right);
}
str _Subtraction::__repr__ () {
  return "-";
}
Expression _Subtraction::derivate (Expression x) {
  return sub(this->left.derivate(x), this->right.derivate(x));
}
Expression _Subtraction::eval (Dict variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return ScalarReal(l.value - r.value);
    };
  return sub(l, r);
}
Expression _Subtraction::full_eval (Dict variables) {
  return this->left.full_eval(variables) - this->right.full_eval(variables);
}
Expression _Subtraction::apply_function (str function) {
  return sub(getattr(this->left, function)(), getattr(this->right, function)());
}
int _Subtraction::_id () {
  return 3;
}
_Multiplication::_Multiplication (Expression left, Expression right) {
  BinaryOperator->__init__(this, left, right);
}
str _Multiplication::__str__ () {
  return this->left._print() + " * " + this->right._print();
}
str _Multiplication::__repr__ () {
  return "*";
}
Expression _Multiplication::derivate (Expression x) {
  return add(mult(this->left, this->right.derivate(x)), mult(this->right, this->left.derivate(x)));
}
Expression _Multiplication::eval (Dict variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return scalar(l.value * r.value);
    };
  return mult(l, r);
}
Expression _Multiplication::full_eval (Dict variables) {
  return this->left.full_eval(variables) * this->right.full_eval(variables);
}
Expression _Multiplication::apply_function (str function) {
  return mult(getattr(this->left, function)(), getattr(this->right, function)());
}
Expression _Multiplication::copy () {
  return this->apply_function("copy");
}
Expression _Multiplication::simplify () {
  return this->apply_function("simplify");
}
Expression _Multiplication::develop () {
      if (isinstance(this->right, Addition)) {
      return this->left * this->right.left + this->left * this->right.right;
    };
      if (isinstance(this->left, Addition)) {
      return this->right * this->left.left + this->right * this->left.right;
    };
}
int _Multiplication::_id () {
  return 4;
}
_Exp::_Exp (Expression expr) {
  UnaryOperator->__init__(this, expr);
}
str _Exp::__str__ () {
  return "exp(" + str(this->expr) + ")";
}
str _Exp::__repr__ () {
  return "exp";
}
Expression _Exp::derivate (Expression x) {
  return mult(this->expr.derivate(x), this);
}
Expression _Exp::eval (Dict variables) {
  auto l = this->expr.eval(variables);
      if (l.is_scalar()) {
      return scalar(math.exp(l.value));
    };
  return exp(l);
}
Expression _Exp::full_eval (Dict variables) {
  return math.exp(this->expr.full_eval(variables));
}
void _Exp::apply_function (str function) {
  return exp(getattr(this->expr, function)());
}
Expression _Exp::cancel () {
  return log(this->expr);
}
int _Exp::_id () {
  return 5;
}
_Log::_Log (Expression expr) {
  UnaryOperator->__init__(this, expr);
}
str _Log::__str__ () {
  return "log(" + str(this->expr) + ")";
}
str _Log::__repr__ () {
  return "log";
}
Expression _Log::derivate (Expression x) {
  return div(this->expr.derivate(x), this->expr);
}
Expression _Log::eval (Dict variables) {
  auto l = this->expr.eval(variables);
      if (l.is_scalar()) {
      return scalar(math.log(l.value));
    };
  return log(l.value);
}
Expression _Log::full_eval (Dict variables) {
  return math.log(this->expr.full_eval(variables));
}
Expression _Log::apply_function (str function) {
  return log(getattr(this->expr, function)());
}
Expression _Log::cancel () {
  return exp(this->expr);
}
int _Log::_id () {
  return 6;
}
_Divide::_Divide (Expression up, Expression down) {
  BinaryOperator->__init__(this, up, down);
}
str _Divide::__str__ () {
  return this->left._print() + " / " + this->right._print();
}
str _Divide::__repr__ () {
  return "/";
}
Expression _Divide::up () {
  return this->left;
}
Expression _Divide::down () {
  return this->right;
}
Expression _Divide::derivate (Expression x) {
  auto a = mult(this->right, this->left.derivate(x));
  auto b = mult(this->left, this->right.derivate(x));
  return div(sub(a, b), pow(this->right, scalar(2)));
}
Expression _Divide::eval (Dict variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return scalar(l.value / r.value);
    };
  return div(l, r);
}
Expression _Divide::full_eval (Dict variables) {
  return this->left.full_eval(variables) / this->right.full_eval(variables);
}
Expression _Divide::apply_function (str function) {
  return div(getattr(this->left, function)(), getattr(this->right, function)());
}
int _Divide::_id () {
  return 7;
}
_Pow::_Pow (Expression expr, Expression power) {
  BinaryOperator->__init__(this, expr, power);
}
Expression _Pow::power () {
  return this->right;
}
Expression _Pow::expr () {
  return this->left;
}
str _Pow::__str__ () {
  return this->left._print() + " ^ " + this->right._print();
}
str _Pow::__repr__ () {
  return "^";
}
Expression _Pow::derivate (Expression x) {
  return mult(mult(this->power(), this->expr().derivate(x)), pow(this->expr(), add(this->power(), minus_one())));
}
Expression _Pow::eval (Dict variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return scalar(pow(l.value, r.value));
    };
  return pow(l, r);
}
Expression _Pow::full_eval (Dict variables) {
  return pow(this->left.full_eval(variables), this->right.full_eval(variables));
}
Expression _Pow::apply_function (str function) {
  return pow(getattr(this->left, function)(), getattr(this->right, function)());
}
int _Pow::_id () {
  return 8;
}
_MathConstant::_MathConstant (str name, float value) {
  ScalarReal->__init__(this, value);
  this->name = name;
}
str _MathConstant::__str__ () {
  return this->name;
}
str _MathConstant::__repr__ () {
  return this->name;
}
void _MathConstant::copy () {
  return this;
}
int _MathConstant::_id () {
  return 9;
}
Expression pi () {
  return __pi;
}
Expression e () {
  return __euler;
}
Expression add (Expression l, Expression r) {
  std::make_tuple(l, r) = reorder(l, r);
    if (l.is_nul()) {
    return r;
  };
    if (r.is_scalar() && l.is_scalar()) {
    return scalar(r.value + l.value);
  };
    if (r == l) {
    return mult(l, scalar(2));
  };
    if (isinstance(l, Subtraction)) {
        if (r == l.right) {
      return l.left;
    };
  };
    if (isinstance(r, Subtraction)) {
        if (l == r.right) {
      return r.left;
    };
  };
    if (isinstance(l, Multiplication)) {
        if (r == l.right && l.left.is_scalar()) {
      return mult(r, scalar(l.left.value + 1));
    };
        if (r == l.left && l.right.is_scalar()) {
      return mult(r, scalar(l.right.value + 1));
    };
  };
    if (isinstance(r, Multiplication)) {
        if (l == r.right && r.left.is_scalar()) {
      return mult(l, scalar(r.left.value + 1));
    };
        if (l == r.left && r.right.is_scalar()) {
      return mult(l, scalar(r.right.value + 1));
    };
  };
  return Addition(l, r);
}
Expression mult (Expression l, Expression r) {
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
    if (r == l) {
    return pow(l, scalar(2));
  };
    if (l.is_scalar() && isinstance(r, Multiplication)) {
        if (r.left.is_scalar()) {
      return mult(scalar(l.value * r.left.value), r.right);
    };
  };
    if (isinstance(l, Divide)) {
        if (r == l.down()) {
      return l.up();
    };
  };
    if (isinstance(r, Divide)) {
        if (l == r.down()) {
      return r.up();
    };
  };
    if (isinstance(l, Pow)) {
        if (r == l.left && l.right.is_scalar()) {
      return pow(r, scalar(l.right.value + 1));
    };
  };
    if (isinstance(r, Pow)) {
        if (l == r.left && r.right.is_scalar()) {
      return pow(l, scalar(r.right.value + 1));
    };
  };
  return Multiplication(l, r);
}
Expression exp (Expression expr) {
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
Expression pow (Expression expr, Expression power) {
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
Expression log (Expression expr) {
    if (expr.is_one()) {
    return zero();
  };
    if (e() == expr) {
    return one();
  };
    if (isinstance(expr, Exp)) {
    return expr.expr;
  };
  return Log(expr);
}
Expression div (Expression up, Expression down) {
    if (down.is_one()) {
    return up;
  };
    if (down == up) {
    return one();
  };
    if (up.is_nul()) {
    return zero();
  };
    if (up.is_scalar() && down.is_scalar()) {
    auto rv = down.value;
    auto lv = up.value;
        if (0 == rv - int(rv) && 0 == lv - int(lv)) {
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
        if (down == up.left) {
      return up.right;
    };
        if (down == up.right) {
      return up.left;
    };
  };
    if (isinstance(down, Multiplication)) {
        if (up == down.left) {
      return down.right;
    };
        if (up == down.right) {
      return down.left;
    };
  };
  return Divide(up, down);
}
Expression scalar (float v) {
    if (0 == v) {
    return zero();
  };
    if (1 == v) {
    return one();
  };
    if (- 1 == v) {
    return minus_one();
  };
    if (2 == v) {
    return two();
  };
  return ScalarReal(v);
}
Expression sub (Expression l, Expression r) {
    if (r == l) {
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
        if (l.right == r) {
      return l.left;
    };
        if (l.left == r) {
      return l.right;
    };
  };
  return Subtraction(l, r);
}

} // symdiff::expression