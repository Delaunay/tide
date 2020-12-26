#ifndef SYMDIFF_EXPRESSION_HEADER
#define SYMDIFF_EXPRESSION_HEADER

#include "kiwi"
#include <cmath>

namespace symdiff::expression {

struct _Expression;
using Expression = std::shared_ptr<_Expression>;
struct _Expression {

  _Expression ();
  virtual str __repr__ ();
  virtual str __str__ ();
  virtual bool __eq__ (Expression other);
  virtual Expression derivate (str x);
  virtual bool is_scalar ();
  virtual bool is_one ();
  virtual bool is_nul ();
  virtual bool is_leaf ();
  virtual Expression eval (Dict variables);
  virtual float full_eval (Dict variables);
  virtual Expression __mul__ (Expression other);
  virtual Expression __add__ (Expression other);
  virtual Expression __truediv__ (Expression other);
  virtual Expression __pow__ (Expression other);
  virtual Expression __sub__ (Expression other);
  virtual Expression __neg__ ();
  virtual void variables ();
  virtual void get_tree ();
  virtual Expression apply_function (str function);
  virtual Expression copy ();
  virtual Expression simplify ();
  virtual Expression develop ();
  virtual Expression factorize ();
  virtual Expression cancel ();
  virtual void _print ();
  virtual int _id ();
  virtual bool __lt__ (Expression other);
};
template<class... Args>
Expression expression(Args&&... args){
   return std::make_shared<_Expression>(std::forward(args)...);
}
Tuple reorder (Expression a, Expression b);
struct _UnaryOperator;
using UnaryOperator = std::shared_ptr<_UnaryOperator>;
struct _UnaryOperator: public Expression {
  Expression expr;

  _UnaryOperator (Expression expr);
  virtual bool __eq__ (Expression other);
  virtual void variables ();
  virtual void get_tree ();
};
template<class... Args>
UnaryOperator unaryoperator(Args&&... args){
   return std::make_shared<_UnaryOperator>(std::forward(args)...);
}
struct _BinaryOperator;
using BinaryOperator = std::shared_ptr<_BinaryOperator>;
struct _BinaryOperator: public Expression {
  Expression left;
  Expression right;

  _BinaryOperator (Expression left, Expression right);
  virtual bool __eq__ (Expression other);
  virtual void variables ();
  virtual void get_tree ();
};
template<class... Args>
BinaryOperator binaryoperator(Args&&... args){
   return std::make_shared<_BinaryOperator>(std::forward(args)...);
}
struct _ScalarReal;
using ScalarReal = std::shared_ptr<_ScalarReal>;
struct _ScalarReal: public Expression {
  float value;

  _ScalarReal (float value);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression __neg__ ();
  virtual bool __eq__ (Expression other);
  virtual bool is_scalar ();
  virtual bool is_one ();
  virtual bool is_nul ();
  virtual bool is_leaf ();
  virtual Expression derivate (Expression x);
  virtual void eval (Dict variables);
  virtual Expression full_eval (Dict variables);
  virtual Expression apply_function (str function);
  virtual int _id ();
};
template<class... Args>
ScalarReal scalarreal(Args&&... args){
   return std::make_shared<_ScalarReal>(std::forward(args)...);
}
Expression one ();
Expression zero ();
Expression minus_one ();
Expression two ();
struct _Unknown;
using Unknown = std::shared_ptr<_Unknown>;
struct _Unknown: public Expression {
  str name;
  int size;

  _Unknown (str name, tuple size);
  virtual str __repr__ ();
  virtual str __hash__ ();
  virtual str __str__ ();
  virtual int _id ();
  virtual bool is_leaf ();
  virtual Expression derivate (Expression x);
  virtual Expression eval (Dict variables);
  virtual Expression full_eval (Dict variables);
  virtual void variables ();
};
template<class... Args>
Unknown unknown(Args&&... args){
   return std::make_shared<_Unknown>(std::forward(args)...);
}
struct _Addition;
using Addition = std::shared_ptr<_Addition>;
struct _Addition: public BinaryOperator {

  _Addition (Expression left, Expression right);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression derivate (Expression x);
  virtual Expression eval (Dict variables);
  virtual Expression full_eval (Dict variables);
  virtual void apply_function (str function);
  virtual int _id ();
};
template<class... Args>
Addition addition(Args&&... args){
   return std::make_shared<_Addition>(std::forward(args)...);
}
struct _Subtraction;
using Subtraction = std::shared_ptr<_Subtraction>;
struct _Subtraction: public BinaryOperator {

  _Subtraction (Expression left, Expression right);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression derivate (Expression x);
  virtual Expression eval (Dict variables);
  virtual Expression full_eval (Dict variables);
  virtual Expression apply_function (str function);
  virtual int _id ();
};
template<class... Args>
Subtraction subtraction(Args&&... args){
   return std::make_shared<_Subtraction>(std::forward(args)...);
}
struct _Multiplication;
using Multiplication = std::shared_ptr<_Multiplication>;
struct _Multiplication: public BinaryOperator {

  _Multiplication (Expression left, Expression right);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression derivate (Expression x);
  virtual Expression eval (Dict variables);
  virtual Expression full_eval (Dict variables);
  virtual Expression apply_function (str function);
  virtual Expression copy ();
  virtual Expression simplify ();
  virtual Expression develop ();
  virtual int _id ();
};
template<class... Args>
Multiplication multiplication(Args&&... args){
   return std::make_shared<_Multiplication>(std::forward(args)...);
}
struct _Exp;
using Exp = std::shared_ptr<_Exp>;
struct _Exp: public UnaryOperator {

  _Exp (Expression expr);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression derivate (Expression x);
  virtual Expression eval (Dict variables);
  virtual Expression full_eval (Dict variables);
  virtual void apply_function (str function);
  virtual Expression cancel ();
  virtual int _id ();
};
template<class... Args>
Exp exp(Args&&... args){
   return std::make_shared<_Exp>(std::forward(args)...);
}
struct _Log;
using Log = std::shared_ptr<_Log>;
struct _Log: public UnaryOperator {

  _Log (Expression expr);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression derivate (Expression x);
  virtual Expression eval (Dict variables);
  virtual Expression full_eval (Dict variables);
  virtual Expression apply_function (str function);
  virtual Expression cancel ();
  virtual int _id ();
};
template<class... Args>
Log log(Args&&... args){
   return std::make_shared<_Log>(std::forward(args)...);
}
struct _Divide;
using Divide = std::shared_ptr<_Divide>;
struct _Divide: public BinaryOperator {

  _Divide (Expression up, Expression down);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression up ();
  virtual Expression down ();
  virtual Expression derivate (Expression x);
  virtual Expression eval (Dict variables);
  virtual Expression full_eval (Dict variables);
  virtual Expression apply_function (str function);
  virtual int _id ();
};
template<class... Args>
Divide divide(Args&&... args){
   return std::make_shared<_Divide>(std::forward(args)...);
}
struct _Pow;
using Pow = std::shared_ptr<_Pow>;
struct _Pow: public BinaryOperator {

  _Pow (Expression expr, Expression power);
  virtual Expression power ();
  virtual Expression expr ();
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression derivate (Expression x);
  virtual Expression eval (Dict variables);
  virtual Expression full_eval (Dict variables);
  virtual Expression apply_function (str function);
  virtual int _id ();
};
template<class... Args>
Pow pow(Args&&... args){
   return std::make_shared<_Pow>(std::forward(args)...);
}
struct _MathConstant;
using MathConstant = std::shared_ptr<_MathConstant>;
struct _MathConstant: public ScalarReal {
  str name;

  _MathConstant (str name, float value);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual void copy ();
  virtual int _id ();
};
template<class... Args>
MathConstant mathconstant(Args&&... args){
   return std::make_shared<_MathConstant>(std::forward(args)...);
}
Expression pi ();
Expression e ();
Expression add (Expression l, Expression r);
Expression mult (Expression l, Expression r);
Expression exp (Expression expr);
Expression pow (Expression expr, Expression power);
Expression log (Expression expr);
Expression div (Expression up, Expression down);
Expression scalar (float v);
Expression sub (Expression l, Expression r);

} // symdiff::expression
#endif