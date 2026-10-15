struct Pair { unsigned int a; unsigned int b; };
struct Container { unsigned int pad; Pair p; };

extern "C" void func_613a0a50(Container *c, Pair p) {
    c->p = p;
}