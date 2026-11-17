extern "C" char D_6175a50c[];

extern "C" void func_6043b488(void *);

extern "C" void func_6042bad8(void **p)
{
    *p = D_6175a50c + 8;
    func_6043b488(p);
}