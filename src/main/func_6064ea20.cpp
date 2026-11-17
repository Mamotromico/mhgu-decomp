extern "C" void func_606026bc(void *);

struct Inner98 {
    char pad[0x98];
    void (*fn)(void *);
};

struct Outer {
    Inner98 *p;
};

extern "C" void func_6064ea20(Outer *o)
{
    func_606026bc(o);
    Inner98 *p = o->p;
    void (*f)(void *) = p->fn;
    f(o);
}