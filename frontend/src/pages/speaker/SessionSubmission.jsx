import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import FileUpload from '../../components/FileUpload';
import {
  Plus,
  X,
  Save,
  Send,
  AlertCircle,
  FileText,
  Users,
  Clock,
  Tag,
} from 'lucide-react';

const SessionSubmission = () => {
  const { user, apiCall } = useAuth();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    session_type_id: '',
    duration_minutes: 45,
    additional_speakers: [],
    upload_comments: '',
    target_audience: '',
    learning_objectives: '',
    prerequisites: '',
    technical_requirements: '',
  });
  
  const [sessionTypes, setSessionTypes] = useState([]);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSessionTypes();
  }, []);

  const fetchSessionTypes = async () => {
    try {
      const response = await apiCall('/session-types');
      if (response.ok) {
        const data = await response.json();
        setSessionTypes(data.session_types || []);
      }
    } catch (error) {
      console.error('Error fetching session types:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
    setError('');
  };

  const handleSelectChange = (name, value) => {
    setFormData({
      ...formData,
      [name]: value,
    });
    setError('');
  };

  const addAdditionalSpeaker = () => {
    setFormData({
      ...formData,
      additional_speakers: [
        ...formData.additional_speakers,
        { name: '', email: '', organization: '', bio: '' }
      ]
    });
  };

  const removeAdditionalSpeaker = (index) => {
    const newSpeakers = formData.additional_speakers.filter((_, i) => i !== index);
    setFormData({
      ...formData,
      additional_speakers: newSpeakers,
    });
  };

  const updateAdditionalSpeaker = (index, field, value) => {
    const newSpeakers = [...formData.additional_speakers];
    newSpeakers[index][field] = value;
    setFormData({
      ...formData,
      additional_speakers: newSpeakers,
    });
  };

  const validateForm = () => {
    if (!formData.title.trim()) {
      setError('Session title is required');
      return false;
    }
    if (!formData.description.trim()) {
      setError('Session description is required');
      return false;
    }
    if (!formData.session_type_id) {
      setError('Please select a session type');
      return false;
    }
    return true;
  };

  const saveDraft = async () => {
    if (!formData.title.trim()) {
      setError('Please enter a session title before saving');
      return;
    }

    setSaving(true);
    setError('');

    try {
      const sessionData = {
        ...formData,
        status: 'draft',
        file_data: uploadedFile,
      };

      const response = await apiCall('/sessions', {
        method: 'POST',
        body: JSON.stringify(sessionData),
      });

      if (response.ok) {
        const data = await response.json();
        navigate(`/speaker/sessions/${data.session.id}/edit`);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to save draft');
      }
    } catch (error) {
      setError('An unexpected error occurred while saving');
    } finally {
      setSaving(false);
    }
  };

  const submitSession = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      const sessionData = {
        ...formData,
        status: 'submitted',
        file_data: uploadedFile,
        submitted_at: new Date().toISOString(),
      };

      const response = await apiCall('/sessions', {
        method: 'POST',
        body: JSON.stringify(sessionData),
      });

      if (response.ok) {
        const data = await response.json();
        navigate('/speaker', { 
          state: { 
            message: 'Session submitted successfully! You will receive an email confirmation shortly.' 
          }
        });
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to submit session');
      }
    } catch (error) {
      setError('An unexpected error occurred while submitting');
    } finally {
      setLoading(false);
    }
  };

  const selectedSessionType = sessionTypes.find(type => type.id === parseInt(formData.session_type_id));

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Submit New Session</h1>
        <p className="text-muted-foreground mt-2">
          Submit your presentation for Cybercon Melbourne 2025
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FileText className="mr-2 h-5 w-5" />
                Session Information
              </CardTitle>
              <CardDescription>
                Provide the basic details about your session
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Session Title *</Label>
                <Input
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  placeholder="Enter your session title"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Session Description *</Label>
                <Textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Provide a detailed description of your session"
                  rows={4}
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="session_type_id">Session Type *</Label>
                  <Select
                    value={formData.session_type_id}
                    onValueChange={(value) => handleSelectChange('session_type_id', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select session type" />
                    </SelectTrigger>
                    <SelectContent>
                      {sessionTypes.map((type) => (
                        <SelectItem key={type.id} value={type.id.toString()}>
                          <div className="flex items-center justify-between w-full">
                            <span>{type.name}</span>
                            <Badge variant="secondary" className="ml-2">
                              {type.default_duration}min
                            </Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {selectedSessionType && (
                    <p className="text-sm text-muted-foreground">
                      {selectedSessionType.description}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="duration_minutes">Duration (minutes)</Label>
                  <Input
                    id="duration_minutes"
                    name="duration_minutes"
                    type="number"
                    value={formData.duration_minutes}
                    onChange={handleChange}
                    min="15"
                    max="180"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="target_audience">Target Audience</Label>
                <Input
                  id="target_audience"
                  name="target_audience"
                  value={formData.target_audience}
                  onChange={handleChange}
                  placeholder="e.g., Security professionals, Developers, Executives"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="learning_objectives">Learning Objectives</Label>
                <Textarea
                  id="learning_objectives"
                  name="learning_objectives"
                  value={formData.learning_objectives}
                  onChange={handleChange}
                  placeholder="What will attendees learn from this session?"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="prerequisites">Prerequisites</Label>
                <Textarea
                  id="prerequisites"
                  name="prerequisites"
                  value={formData.prerequisites}
                  onChange={handleChange}
                  placeholder="Any required knowledge or experience for attendees"
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="technical_requirements">Technical Requirements</Label>
                <Textarea
                  id="technical_requirements"
                  name="technical_requirements"
                  value={formData.technical_requirements}
                  onChange={handleChange}
                  placeholder="Any special equipment, software, or setup requirements"
                  rows={2}
                />
              </div>
            </CardContent>
          </Card>

          {/* Additional Speakers */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Users className="mr-2 h-5 w-5" />
                Additional Speakers
              </CardTitle>
              <CardDescription>
                Add co-presenters or additional speakers for this session
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {formData.additional_speakers.map((speaker, index) => (
                <div key={index} className="border rounded-lg p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium">Speaker {index + 1}</h4>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeAdditionalSpeaker(index)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Name *</Label>
                      <Input
                        value={speaker.name}
                        onChange={(e) => updateAdditionalSpeaker(index, 'name', e.target.value)}
                        placeholder="Speaker name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Email *</Label>
                      <Input
                        type="email"
                        value={speaker.email}
                        onChange={(e) => updateAdditionalSpeaker(index, 'email', e.target.value)}
                        placeholder="speaker@example.com"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Organization</Label>
                    <Input
                      value={speaker.organization}
                      onChange={(e) => updateAdditionalSpeaker(index, 'organization', e.target.value)}
                      placeholder="Company or organization"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Bio</Label>
                    <Textarea
                      value={speaker.bio}
                      onChange={(e) => updateAdditionalSpeaker(index, 'bio', e.target.value)}
                      placeholder="Brief biography"
                      rows={2}
                    />
                  </div>
                </div>
              ))}
              
              <Button
                variant="outline"
                onClick={addAdditionalSpeaker}
                className="w-full"
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Additional Speaker
              </Button>
            </CardContent>
          </Card>

          {/* File Upload */}
          <Card>
            <CardHeader>
              <CardTitle>Presentation File</CardTitle>
              <CardDescription>
                Upload your presentation file (PDF, PPT, PPTX, MP4, MOV)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FileUpload
                onFileUpload={setUploadedFile}
                existingFile={uploadedFile}
              />
              
              <div className="mt-4 space-y-2">
                <Label htmlFor="upload_comments">Upload Comments</Label>
                <Textarea
                  id="upload_comments"
                  name="upload_comments"
                  value={formData.upload_comments}
                  onChange={handleChange}
                  placeholder="Any additional comments about your presentation file"
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Submission Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                onClick={saveDraft}
                variant="outline"
                className="w-full"
                disabled={saving || loading}
              >
                <Save className="mr-2 h-4 w-4" />
                {saving ? 'Saving...' : 'Save Draft'}
              </Button>
              
              <Button
                onClick={submitSession}
                className="w-full"
                disabled={loading || saving}
              >
                <Send className="mr-2 h-4 w-4" />
                {loading ? 'Submitting...' : 'Submit Session'}
              </Button>
              
              <Separator />
              
              <Button
                variant="ghost"
                onClick={() => navigate('/speaker')}
                className="w-full"
              >
                Cancel
              </Button>
            </CardContent>
          </Card>

          {/* Submission Guidelines */}
          <Card>
            <CardHeader>
              <CardTitle>Submission Guidelines</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="space-y-2">
                <h4 className="font-medium flex items-center">
                  <Clock className="mr-1 h-3 w-3" />
                  Timeline
                </h4>
                <ul className="text-muted-foreground space-y-1 ml-4">
                  <li>• Review process: 2-3 weeks</li>
                  <li>• Notification by: March 15, 2025</li>
                  <li>• Final materials due: April 1, 2025</li>
                </ul>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium flex items-center">
                  <FileText className="mr-1 h-3 w-3" />
                  File Requirements
                </h4>
                <ul className="text-muted-foreground space-y-1 ml-4">
                  <li>• Formats: PDF, PPT, PPTX, MP4, MOV</li>
                  <li>• Maximum size: 100MB</li>
                  <li>• Include speaker notes if applicable</li>
                </ul>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium flex items-center">
                  <Tag className="mr-1 h-3 w-3" />
                  Tips
                </h4>
                <ul className="text-muted-foreground space-y-1 ml-4">
                  <li>• Be specific about learning outcomes</li>
                  <li>• Include practical examples</li>
                  <li>• Consider your audience level</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default SessionSubmission;

