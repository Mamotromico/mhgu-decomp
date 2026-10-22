struct B;
typedef void (*BFn)(B*, int);

struct VTable {
  char pad[0x60];
  BFn func;
};

struct B {
  VTable* vtable;
};

struct A {
  char pad[0x50];
  int field50;
  B* ptr54;
};

extern "C" void func_605cf4e4(A* a, int value) {
  a->field50 = value;
  B* b = a->ptr54;
  b->vtable->func(b, value);
}