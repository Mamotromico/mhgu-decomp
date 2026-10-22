struct Arg1;
typedef void (*Fn)(Arg1*, void*);
struct Arg1 { Fn *vtable; };
struct Arg0 { int pad0; void *field4; };
extern "C" void func_600eb890(Arg0 *a, Arg1 *b) {
    Fn f = b->vtable[3];
    f(b, a->field4);
}