struct S { unsigned int a; unsigned int b; unsigned int c; };

extern "C" void func_613dd68c(unsigned int a, S *p)
{
    *p = S{a, 0, 0};
}