typedef struct {
    char pad0[0x28];
    int field_28;
} S;

extern "C" void func_6056e3b0(S *);
extern "C" void func_605701b0(S *, int);

extern "C" void func_6058a138(S *s)
{
    s->field_28 = 0;
    func_6056e3b0(s);
    func_605701b0(s, 1);
}