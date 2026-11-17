extern "C" {

void func_6056e4d8(void);
void func_60641510(void *);

void func_606414f0(void *p)
{
    func_6056e4d8();
    func_60641510(p);
    *(unsigned *)((char *)p + 0x4c) = 0;
}

}