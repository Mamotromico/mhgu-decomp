extern "C" {

extern char D_6188a7d8[];

void *func_607aa47c(void *);

void func_60381a4c(void *arg)
{
    void *p = func_607aa47c(&D_6188a7d8);
    unsigned *r0 = (unsigned *)p;
    unsigned *r1 = (unsigned *)*r0;
    void (*fn)(void *, void *) = (void (*)(void *, void *))*(unsigned *)((char *)r1 + 0x34);
    fn(p, arg);
}

}