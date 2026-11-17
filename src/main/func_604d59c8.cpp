extern "C" int func_604d59f4(void *p);

extern char D_617694d0[];

extern "C" void *func_604d59c8(void *p)
{
    *(void **)p = &D_617694d0[8];
    func_604d59f4(p);
    return p;
}