extern "C" void func_6056e4d8(void);
extern "C" int func_6058b908(void *p);

extern "C" int func_6058b8f0(void *p)
{
    void *saved = p;
    func_6056e4d8();
    return func_6058b908(saved);
}