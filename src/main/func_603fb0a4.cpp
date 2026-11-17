extern "C" char D_61755500[];

struct S_603fb0a4 {
    void *field_0;
};

extern "C" void func_6043b488(S_603fb0a4 *);

extern "C" void func_603fb0a4(S_603fb0a4 *s)
{
    s->field_0 = (void *)&D_61755500[8];
    func_6043b488(s);
}