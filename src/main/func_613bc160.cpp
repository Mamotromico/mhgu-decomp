extern "C" unsigned func_607aef68(unsigned);

struct S { char pad[4]; unsigned field; };

extern "C" void func_613bc160(void *p, unsigned x)
{
    ((S *)p)->field = func_607aef68(x);
}