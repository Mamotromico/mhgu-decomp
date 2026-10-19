struct Pair { int a; int b; };
struct Obj { Pair p; int v; };

extern "C" void func_6122f7d0(Obj *obj, int, Pair src) {
    obj->p = src;
    obj->v = 6;
}