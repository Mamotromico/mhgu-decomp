extern "C" char D_6173fcc8[];
extern "C" void func_601a8540(void *);

extern "C" void *func_601a8514(void *p)
{
    *(void **)p = (void *)((char *)D_6173fcc8 + 8);
    func_601a8540(p);
    return p;
}