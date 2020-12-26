#ifndef None
#define None

#include "math.h"
struct _Expression {

  _Expression ();
  void __repr__ ();
  void __str__ ();
  bool __eq__ (Expression other);
  void derivate (str x);
  void is_scalar ();
  void is_one ();
  void is_nul ();
  void is_leaf ();
  void eval (Dict variables);
  void full_eval (dict variables);
  void __mul__ (Expression other);
  void __add__ (Expression other);
  void __truediv__ (Expression other);
  void __pow__ (Expression other);
  void __sub__ (Expression other);
  void __neg__ ();
  void variables ();
  void get_tree ();
  void apply_function (Callable function);
  void copy ();
  void simplify ();
  void develop ();
  void factorize ();
  void cancel ();
  void primitive (str x);
  void _print ();
  void _id ();
  void __lt__ (Expression other);
};
using Expression = std::shared_ptr<_Expression>
template<class... Args>
Expression expression(Args&&... args){
   return make_shared<_Expression>(std::forward(args)...);
}
void reorder (Expression a, Expression b);
struct _UnaryOperator: public Expression {
  Expression expr;

  _UnaryOperator (Expression expr);
  bool __eq__ (Expression other);
  void variables ();
  void get_tree ();
};
using UnaryOperator = std::shared_ptr<_UnaryOperator>
template<class... Args>
UnaryOperator unaryoperator(Args&&... args){
   return make_shared<_UnaryOperator>(std::forward(args)...);
}
struct _BinaryOperator: public Expression {
  Expression left;
  Expression right;

  _BinaryOperator (Expression left, Expression right);
  bool __eq__ (Expression other);
  void variables ();
  void get_tree ();
};
using BinaryOperator = std::shared_ptr<_BinaryOperator>
template<class... Args>
BinaryOperator binaryoperator(Args&&... args){
   return make_shared<_BinaryOperator>(std::forward(args)...);
}
struct _ScalarReal: public Expression {
  float value;

  _ScalarReal (float value);
  void __str__ ();
  void __repr__ ();
  void __neg__ ();
  void __eq__ (Expression other);
  void is_scalar ();
  void is_one ();
  void is_nul ();
  void is_leaf ();
  Expression derivate (Expression x);
  void eval (None variables);
  Expression full_eval (Dict variables);
  void apply_function (None function);
  void primitive (None x);
  void _id ();
};
using ScalarReal = std::shared_ptr<_ScalarReal>
template<class... Args>
ScalarReal scalarreal(Args&&... args){
   return make_shared<_ScalarReal>(std::forward(args)...);
}
void one ();
void zero ();
void minus_one ();
void two ();
struct _Unknown: public Expression {
  str name;
  int size;

  _Unknown (str name, tuple size);
  void __repr__ ();
  void __hash__ ();
  void __str__ ();
  void _id ();
  void is_leaf ();
  Expression derivate (Expression x);
  Expression eval (None variables);
  Expression full_eval (None variables);
  void variables ();
  void primitive (None x);
};
using Unknown = std::shared_ptr<_Unknown>
template<class... Args>
Unknown unknown(Args&&... args){
   return make_shared<_Unknown>(std::forward(args)...);
}
struct _Addition: public BinaryOperator {

  _Addition (Expression left, Expression right);
  void __str__ ();
  void __repr__ ();
  Expression derivate (Expression x);
  Expression eval (None variables);
  Expression full_eval (None variables);
  void apply_function (None function);
  void primitive (None x);
  void _id ();
};
using Addition = std::shared_ptr<_Addition>
template<class... Args>
Addition addition(Args&&... args){
   return make_shared<_Addition>(std::forward(args)...);
}
struct _Subtraction: public BinaryOperator {

  _Subtraction (Expression left, Expression right);
  void __str__ ();
  void __repr__ ();
  Expression derivate (Expression x);
  Expression eval (None variables);
  Expression full_eval (None variables);
  void apply_function (None function);
  void primitive (None x);
  void _id ();
};
using Subtraction = std::shared_ptr<_Subtraction>
template<class... Args>
Subtraction subtraction(Args&&... args){
   return make_shared<_Subtraction>(std::forward(args)...);
}
struct _Multiplication: public BinaryOperator {

  _Multiplication (Expression left, Expression right);
  void __str__ ();
  void __repr__ ();
  Expression derivate (Expression x);
  Expression eval (None variables);
  Expression full_eval (None variables);
  void apply_function (None function);
  void copy ();
  void simplify ();
  void develop ();
  void primitive (None x);
  void _id ();
};
using Multiplication = std::shared_ptr<_Multiplication>
template<class... Args>
Multiplication multiplication(Args&&... args){
   return make_shared<_Multiplication>(std::forward(args)...);
}
struct _Exp: public UnaryOperator {

  _Exp (Expression expr);
  void __str__ ();
  void __repr__ ();
  Expression derivate (Expression x);
  Expression eval (None variables);
  Expression full_eval (None variables);
  void apply_function (None function);
  void cancel ();
  void primitive (None x);
  void _id ();
};
using Exp = std::shared_ptr<_Exp>
template<class... Args>
Exp exp(Args&&... args){
   return make_shared<_Exp>(std::forward(args)...);
}
struct _Log: public UnaryOperator {

  _Log (Expression expr);
  void __str__ ();
  void __repr__ ();
  Expression derivate (Expression x);
  Expression eval (None variables);
  Expression full_eval (None variables);
  void apply_function (None function);
  void cancel ();
  void primitive (None x);
  void _id ();
};
using Log = std::shared_ptr<_Log>
template<class... Args>
Log log(Args&&... args){
   return make_shared<_Log>(std::forward(args)...);
}
struct _Divide: public BinaryOperator {

  _Divide (Expression up, Expression down);
  void __str__ ();
  void __repr__ ();
  void up ();
  void down ();
  Expression derivate (Expression x);
  Expression eval (None variables);
  Expression full_eval (None variables);
  void apply_function (None function);
  void _id ();
};
using Divide = std::shared_ptr<_Divide>
template<class... Args>
Divide divide(Args&&... args){
   return make_shared<_Divide>(std::forward(args)...);
}
struct _Pow: public BinaryOperator {

  _Pow (Expression expr, Expression power);
  void power ();
  void expr ();
  void __str__ ();
  void __repr__ ();
  Expression derivate (Expression x);
  Expression eval (None variables);
  Expression full_eval (None variables);
  void apply_function (None function);
  void primitive (None x);
  void _id ();
};
using Pow = std::shared_ptr<_Pow>
template<class... Args>
Pow pow(Args&&... args){
   return make_shared<_Pow>(std::forward(args)...);
}
struct _MathConstant: public ScalarReal {
  str name;

  _MathConstant (None name, None value);
  void __str__ ();
  void __repr__ ();
  void copy ();
  void _id ();
};
using MathConstant = std::shared_ptr<_MathConstant>
template<class... Args>
MathConstant mathconstant(Args&&... args){
   return make_shared<_MathConstant>(std::forward(args)...);
}
void pi ();
void e ();
Expression add (Expression l, Expression r);
Expression mult (Expression l, Expression r);
Expression exp (Expression expr);
Expression pow (Expression expr, Expression power);
Expression log (Expression expr);
Expression div (Expression up, Expression down);
void scalar (None v);
Expression sub (Expression l, Expression r);
void apply_operator (None l, None r, None f);
#endif