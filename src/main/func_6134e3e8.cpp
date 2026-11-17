typedef struct { char pad[0x1000]; } Unk;

extern "C" void func_6134cce8(Unk *p);
extern "C" void func_6134e400(Unk *p);

extern "C" void func_6134e3e8(Unk *p)
{
    func_6134cce8(p);
    func_6134e400(p);
}