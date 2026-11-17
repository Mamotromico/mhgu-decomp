extern "C" void func_6056e4d8(void *);
extern "C" void func_6064bc40(void *);
extern "C" void func_6064be64(void *);

extern "C" void func_6064bc18(void *p)
{
    func_6056e4d8(p);
    func_6064bc40(p);
    func_6064be64(p);
    *(unsigned char *)((char *)p + 0x6f) = 0;
}