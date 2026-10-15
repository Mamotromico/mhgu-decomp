extern "C" {

struct Payload {
    char pad0[0x74];
    float value;
};

void func_6095fee0(Payload *p, float v)
{
    p->value = v;
}

}