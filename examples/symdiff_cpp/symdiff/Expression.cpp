#include "Expression.h"

namespace symdiff::Expression {

_Expression::_Expression () {

}
_Expression::void __repr__ () {
  return "FAIL";
}
_Expression::void __str__ () {

}
_Expression::bool __eq__ (Expression other) {
      if (other == self) {
      return true;
    };
  return false;
}
_Expression::void derivate (str x) {
  " derivate in respect of x";
  return self;
}
_Expression::void is_scalar () {
  return false;
}
_Expression::void is_one () {
  return false;
}
_Expression::void is_nul () {
  return false;
}
_Expression::void is_leaf () {
  return false;
}
_Expression::void eval (Dict variables) {
  " partially evaluate the expression";
}
_Expression::void full_eval (dict variables) {
  " fully evaluate the expression, every unknown must be specified";
}
_Expression::void __mul__ (Expression other) {
  return apply_operator(self, other, mult);
}
_Expression::void __add__ (Expression other) {
  return apply_operator(self, other, add);
}
_Expression::void __truediv__ (Expression other) {
  return apply_operator(self, other, div);
}
_Expression::void __pow__ (Expression other) {
  return apply_operator(self, other, pow);
}
_Expression::void __sub__ (Expression other) {
  return apply_operator(self, other, sub);
}
_Expression::void __neg__ () {
  " return - self";
  return mult(minus_one(), self);
}
_Expression::void variables () {
  " Return a set of unknown the expression depend of";
  return set();
}
_Expression::void get_tree () {
  " Return Operation tree";
  return std::vector<>{};
}
_Expression::void apply_function (Callable function) {
  " apply a function to the graph ";
  return self;
}
_Expression::void copy () {
  " return a copy of the expression";
  return this->apply_function("copy");
}
_Expression::void simplify () {
  return this->apply_function("simplify");
}
_Expression::void develop () {
  return this->apply_function("develop");
}
_Expression::void factorize () {
  return this->apply_function("factorize");
}
_Expression::void cancel () {
  " return the expression cancelling the current expression
            i.e x => 1/x     exp => log    x ** 2 => x ** 0.5 ";
  return self;
}
_Expression::void primitive (str x) {
  return self;
}
_Expression::void _print () {
      if (this->is_leaf()) {
      return this->__str__();
    };
  return "(" + this->__str__() + ")";
}
_Expression::void _id () {
  throw None;
}
_Expression::void __lt__ (Expression other) {
  return other._id() < this->_id();
}
void reorder (Expression a, Expression b) {
  auto ia = a._id();
  auto ib = b._id();
    if (ib < ia) {
    return std::tuple<>{a, b};
  };
    if (ib != ia) {
    return std::tuple<>{b, a};
  };
    if (a.is_scalar() && b.is_scalar() && b.value > a.value) {
    return std::tuple<>{b, a};
  };
  return std::tuple<>{a, b};
}
_UnaryOperator::_UnaryOperator (Expression expr) {
  Expression->__init__(self);
  this->expr = expr;
}
_UnaryOperator::bool __eq__ (Expression other) {
      if (other == self) {
      return true;
    };
      if (isinstance(other, type(self))) {
            if (other.expr == this->expr) {
        return true;
      };
    };
  return false;
}
_UnaryOperator::void variables () {
  return this->expr.variables();
}
_UnaryOperator::void get_tree () {
  return std::vector<>{self} + this->expr.get_tree();
}
_BinaryOperator::_BinaryOperator (Expression left, Expression right) {
  Expression->__init__(self);
  this->left = left;
  this->right = right;
}
_BinaryOperator::bool __eq__ (Expression other) {
      if (other == self) {
      return true;
    };
      if (isinstance(other, type(self))) {
            if (other.left == this->left && other.right == this->right) {
        return true;
      };
    };
  return false;
}
_BinaryOperator::void variables () {
  return this->left.variables().union(this->right.variables());
}
_BinaryOperator::void get_tree () {
  return std::vector<>{self} + this->left.get_tree() + this->right.get_tree();
}
_ScalarReal::_ScalarReal (float value) {
  Expression->__init__(self);
  this->value = value;
}
_ScalarReal::void __str__ () {
  return str(this->value);
}
_ScalarReal::void __repr__ () {
  return "Scalar<" + str(this->value) + ">";
}
_ScalarReal::void __neg__ () {
  return scalar(- this->value);
}
_ScalarReal::void __eq__ (Expression other) {
      if (other == self) {
      return true;
    };
      if (isinstance(other, ScalarReal) && this->value == other.value) {
      return true;
    };
  return false;
}
_ScalarReal::void is_scalar () {
  return true;
}
_ScalarReal::void is_one () {
  return 1 == this->value;
}
_ScalarReal::void is_nul () {
  return 0 == this->value;
}
_ScalarReal::void is_leaf () {
  return true;
}
_ScalarReal::Expression derivate (Expression x) {
  return zero();
}
_ScalarReal::void eval (None variables) {
      if (this->is_one()) {
      return one();
    };
      if (this->is_nul()) {
      return zero();
    };
  return self;
}
_ScalarReal::Expression full_eval (Dict variables) {
  return this->value;
}
_ScalarReal::void apply_function (None function) {
  return scalar(this->value);
}
_ScalarReal::void primitive (None x) {
  return mult(self, x);
}
_ScalarReal::void _id () {
  return 0;
}
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
_Unknown::_Unknown (str name, tuple size) {
  Expression->__init__(self);
  this->name = name;
  this->size = size;
}
_Unknown::void __repr__ () {
  return this->name + str(this->size);
}
_Unknown::void __hash__ () {
  return str.__hash__(this->name);
}
_Unknown::void __str__ () {
  return this->name;
}
_Unknown::void _id () {
  return 1;
}
_Unknown::void is_leaf () {
  return true;
}
_Unknown::Expression derivate (Expression x) {
      if (self == x) {
      return one();
    };
  return zero();
}
_Unknown::Expression eval (None variables) {
      if (contains(self, variables)) {
      return variables;
    };
  return self;
}
_Unknown::Expression full_eval (None variables) {
  return variables.full_eval(variables);
}
_Unknown::void variables () {
  return std::set<>self;
}
_Unknown::void primitive (None x) {
      if (self == x) {
      return pow(mult(div(one(), two()), self), two());
    };
  return mult(self, x);
}
_Addition::_Addition (Expression left, Expression right) {
  BinaryOperator->__init__(self, left, right);
}
_Addition::void __str__ () {
  return str(this->left) + " + " + str(this->right);
}
_Addition::void __repr__ () {
  return "+";
}
_Addition::Expression derivate (Expression x) {
  return add(this->left.derivate(x), this->right.derivate(x));
}
_Addition::Expression eval (None variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return scalar(l.value + r.value);
    };
  return add(l, r);
}
_Addition::Expression full_eval (None variables) {
  return this->left.full_eval(variables) + this->right.full_eval(variables);
}
_Addition::void apply_function (None function) {
  return add(getattr(this->left, function)(), getattr(this->right, function)());
}
_Addition::void primitive (None x) {
  return add(this->left.primitive(x), this->right.primitive(x));
}
_Addition::void _id () {
  return 2;
}
_Subtraction::_Subtraction (Expression left, Expression right) {
  BinaryOperator->__init__(self, left, right);
}
_Subtraction::void __str__ () {
  return str(this->left) + " - " + str(this->right);
}
_Subtraction::void __repr__ () {
  return "-";
}
_Subtraction::Expression derivate (Expression x) {
  return sub(this->left.derivate(x), this->right.derivate(x));
}
_Subtraction::Expression eval (None variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return ScalarReal(l.value - r.value);
    };
  return sub(l, r);
}
_Subtraction::Expression full_eval (None variables) {
  return this->left.full_eval(variables) - this->right.full_eval(variables);
}
_Subtraction::void apply_function (None function) {
  return sub(getattr(this->left, function)(), getattr(this->right, function)());
}
_Subtraction::void primitive (None x) {
  return sub(this->left.primitive(x), this->right.primitive(x));
}
_Subtraction::void _id () {
  return 3;
}
_Multiplication::_Multiplication (Expression left, Expression right) {
  BinaryOperator->__init__(self, left, right);
}
_Multiplication::void __str__ () {
  return this->left._print() + " * " + this->right._print();
}
_Multiplication::void __repr__ () {
  return "*";
}
_Multiplication::Expression derivate (Expression x) {
  return add(mult(this->left, this->right.derivate(x)), mult(this->right, this->left.derivate(x)));
}
_Multiplication::Expression eval (None variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return scalar(l.value * r.value);
    };
  return mult(l, r);
}
_Multiplication::Expression full_eval (None variables) {
  return this->left.full_eval(variables) * this->right.full_eval(variables);
}
_Multiplication::void apply_function (None function) {
  return mult(getattr(this->left, function)(), getattr(this->right, function)());
}
_Multiplication::void copy () {
  return this->apply_function("copy");
}
_Multiplication::void simplify () {
  return this->apply_function("simplify");
}
_Multiplication::void develop () {
      if (isinstance(this->right, Addition)) {
      return this->left * this->right.left + this->left * this->right.right;
    };
      if (isinstance(this->left, Addition)) {
      return this->right * this->left.left + this->right * this->left.right;
    };
}
_Multiplication::void primitive (None x) {

}
_Multiplication::void _id () {
  return 4;
}
_Exp::_Exp (Expression expr) {
  UnaryOperator->__init__(self, expr);
}
_Exp::void __str__ () {
  return "exp(" + str(this->expr) + ")";
}
_Exp::void __repr__ () {
  return "exp";
}
_Exp::Expression derivate (Expression x) {
  return mult(this->expr.derivate(x), self);
}
_Exp::Expression eval (None variables) {
  auto l = this->expr.eval(variables);
      if (l.is_scalar()) {
      return scalar(math.exp(l.value));
    };
  return exp(l);
}
_Exp::Expression full_eval (None variables) {
  return math.exp(this->expr.full_eval(variables));
}
_Exp::void apply_function (None function) {
  return exp(getattr(this->expr, function)());
}
_Exp::void cancel () {
  return log(this->expr);
}
_Exp::void primitive (None x) {
  return self;
}
_Exp::void _id () {
  return 5;
}
_Log::_Log (Expression expr) {
  UnaryOperator->__init__(self, expr);
}
_Log::void __str__ () {
  return "log(" + str(this->expr) + ")";
}
_Log::void __repr__ () {
  return "log";
}
_Log::Expression derivate (Expression x) {
  return div(this->expr.derivate(x), this->expr);
}
_Log::Expression eval (None variables) {
  auto l = this->expr.eval(variables);
      if (l.is_scalar()) {
      return scalar(math.log(l.value));
    };
  return log(l.value);
}
_Log::Expression full_eval (None variables) {
  return math.log(this->expr.full_eval(variables));
}
_Log::void apply_function (None function) {
  return log(getattr(this->expr, function)());
}
_Log::void cancel () {
  return exp(this->expr);
}
_Log::void primitive (None x) {
  throw None;
}
_Log::void _id () {
  return 6;
}
_Divide::_Divide (Expression up, Expression down) {
  BinaryOperator->__init__(self, up, down);
}
_Divide::void __str__ () {
  return this->left._print() + " / " + this->right._print();
}
_Divide::void __repr__ () {
  return "/";
}
_Divide::void up () {
  return this->left;
}
_Divide::void down () {
  return this->right;
}
_Divide::Expression derivate (Expression x) {
  auto a = mult(this->right, this->left.derivate(x));
  auto b = mult(this->left, this->right.derivate(x));
  return div(sub(a, b), pow(this->right, scalar(2)));
}
_Divide::Expression eval (None variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return scalar(l.value / r.value);
    };
  return div(l, r);
}
_Divide::Expression full_eval (None variables) {
  return this->left.full_eval(variables) / this->right.full_eval(variables);
}
_Divide::void apply_function (None function) {
  return div(getattr(this->left, function)(), getattr(this->right, function)());
}
_Divide::void _id () {
  return 7;
}
_Pow::_Pow (Expression expr, Expression power) {
  BinaryOperator->__init__(self, expr, power);
}
_Pow::void power () {
  return this->right;
}
_Pow::void expr () {
  return this->left;
}
_Pow::void __str__ () {
  return this->left._print() + " ^ " + this->right._print();
}
_Pow::void __repr__ () {
  return "^";
}
_Pow::Expression derivate (Expression x) {
  return mult(mult(this->power(), this->expr().derivate(x)), pow(this->expr(), add(this->power(), minus_one())));
}
_Pow::Expression eval (None variables) {
  auto l = this->left.eval(variables);
  auto r = this->right.eval(variables);
      if (l.is_scalar() && r.is_scalar()) {
      return scalar(pow(l.value, r.value));
    };
  return pow(l, r);
}
_Pow::Expression full_eval (None variables) {
  return pow(this->left.full_eval(variables), this->right.full_eval(variables));
}
_Pow::void apply_function (None function) {
  return pow(getattr(this->left, function)(), getattr(this->right, function)());
}
_Pow::void primitive (None x) {
  auto v = this->power() + one();
  return mult(div(one(), v), pow(this->expr(), v));
}
_Pow::void _id () {
  return 8;
}
_MathConstant::_MathConstant (None name, None value) {
  ScalarReal->__init__(self, value);
  this->name = name;
}
_MathConstant::void __str__ () {
  return this->name;
}
_MathConstant::void __repr__ () {
  return this->name;
}
_MathConstant::void copy () {
  return self;
}
_MathConstant::void _id () {
  return 9;
}
void pi () {
  return __pi;
}
void e () {
  return __euler;
}
Expression add (Expression l, Expression r) {
  std::tuple<>{l, r} = reorder(l, r);
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
  std::tuple<>{l, r} = reorder(l, r);
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
void scalar (None v) {
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
void apply_operator (None l, None r, None f) {
    if (isinstance(r, Expression)) {
    return f(l, r);
  };
  return f(l, scalar(r));
}

} // symdiff::Expression