import unittest
from terminology import normalize,required_turkish

class TerminologyTests(unittest.TestCase):
 def test_parameter_number_and_length_cannot_be_collapsed_into_one(self):
  terms=required_turkish('Block and stack methods do not limit the number or length of parameters.')
  self.assertIn('sayı',terms);self.assertIn('uzunlu',terms)
  self.assertNotIn('uzunlu',required_turkish('There is no limit on the number of parameters.'))
 def test_process_type_is_not_an_invented_named_call(self):
  result,edits=normalize('There is a process control system called type and it creates a process.')
  self.assertIn('a type of process control system call',result);self.assertEqual(len(edits),1)
  self.assertEqual(normalize('The system call type() is defined.')[0],'The system call type() is defined.')
 def test_device_operations_require_their_context(self):
  source='Get device, locally, attack or detect devices.'
  self.assertEqual(normalize(source)[0],source)
  self.assertIn('logically attach or detach devices',normalize(source,'device management')[0])
 def test_remote_devices_and_message_passing_need_communication_context(self):
  source='Communication: passing Passing model, shared memory model, attack and detect remote devices.'
  result,_=normalize(source)
  self.assertIn('message-passing model',result)
  self.assertIn('attach and detach remote devices',result)
  security='Cybersecurity: locally attack or detect devices. Device management.'
  self.assertEqual(normalize(security)[0],security)
 def test_logs_remain_logs_when_they_record_events(self):
  source='Logs record access to shared data between processes.'
  self.assertEqual(normalize(source)[0],source)
  self.assertIn('locks for managing',normalize('logs for managing access to shared data between processes')[0])
 def test_real_html_is_never_replaced(self):
  source='HTML is a markup language.'
  self.assertEqual(normalize(source,'What is HTML?')[0],source)
  self.assertEqual(normalize('It is HTML in Turkish.','What is the process?')[0],'It is işlem in Turkish.')
  self.assertEqual(normalize('It is HTML in Turkish.','What is the process? What is HTML?')[0],'It is HTML in Turkish.')
 def test_registering_for_exam_is_not_a_hardware_register(self):
  self.assertEqual(required_turkish('Students register for an exam.'),[])
  self.assertIn('yazmaç',required_turkish('Put the parameter in a register.'))
 def test_normalization_is_idempotent_and_preserves_numbers(self):
  source='Device management 13: locally attack or detect devices.'
  normalized,_=normalize(source)
  self.assertEqual(normalize(normalized)[0],normalized);self.assertIn('13',normalized)

if __name__=='__main__':unittest.main()
